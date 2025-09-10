from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.error import HTTPError, URLError

from config import config
from serp_tool.logging import scraper_logger, get_quota_logger
from serp_tool.utils.temp_manager import get_cache_dir
from serp_tool.utils.token_manager import token_manager

from .cache import build_cache_key, read_cache, write_cache
from .http import http_get_json, handle_http_error, log_url_error, is_quota_exceeded_error
from .mapping import map_cse_item_to_search_result


class QuotaExceededError(Exception):
    """Raised when Google CSE API quota is exceeded."""
    def __init__(self, message: str, quota_info: Optional[Dict[str, Any]] = None, help_links: Optional[List[str]] = None):
        super().__init__(message)
        self.quota_info = quota_info or {}
        self.help_links = help_links or []
        self.error_type = "quota_exceeded"


class GoogleCSEClient:
    """Google CSE JSON API client with simple file caching.

    Preserves behavior of the original implementation.
    """

    BASE_URL = None

    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None, cache_ttl_seconds: int = 24 * 3600):
        self.api_key = api_key or config.google_api_key
        self.cx = cx or config.google_cx
        self.BASE_URL = config.google_base_url or "https://www.googleapis.com/customsearch/v1"
        caching = config.caching_settings or {}
        # Use temp_manager for cache directory
        self.cache_dir = get_cache_dir()
        self.cache_ttl = int(caching.get("ttl_seconds", cache_ttl_seconds))
        self._quota_exceeded = False

    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx)
    
    def _try_backup_token_switch(self) -> bool:
        """Try to switch to backup token when quota is exceeded."""
        if not self._quota_exceeded:
            return False
        
        # Try to switch to backup API key
        if token_manager.has_backup_token('google_api_key'):
            success, message = token_manager.switch_to_backup_token('google_api_key')
            if success:
                self.api_key = token_manager.get_token('google_api_key')
                self._quota_exceeded = False
                scraper_logger.info(f"Switched to backup Google API key: {message}")
                return True
            else:
                scraper_logger.warning(f"Failed to switch to backup Google API key: {message}")
        
        return False

    def _get_with_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = build_cache_key(self.cache_dir, params)
        cached = read_cache(path, self.cache_ttl)
        if cached is not None:
            return cached
        try:
            data = http_get_json(self.BASE_URL, params, timeout=max(5, config.request_timeout))
            write_cache(path, data)
            return data
        except HTTPError as e:
            is_quota_error, quota_info = is_quota_exceeded_error(e)
            if is_quota_error:
                self._quota_exceeded = True
                
                # Mark current token as quota exceeded
                if self.api_key:
                    token_manager.mark_token_quota_exceeded('google_api_key', self.api_key)
                
                # Try to switch to backup token
                if self._try_backup_token_switch():
                    # Retry the request with backup token
                    try:
                        data = http_get_json(self.BASE_URL, params, timeout=max(5, config.request_timeout))
                        write_cache(path, data)
                        return data
                    except HTTPError as retry_e:
                        # Backup token also failed, continue with original error
                        pass
                
                # Log quota exceeded with detailed information
                quota_logger = get_quota_logger()
                quota_logger.warning(
                    f"Google CSE quota exceeded: {quota_info.get('error_message', 'Unknown quota error')}",
                    extra={
                        "action": "quota_exceeded", 
                        "status": "fail",
                        "quota_limit": quota_info.get("quota_info", {}).get("quota_limit_value"),
                        "quota_metric": quota_info.get("quota_info", {}).get("quota_metric"),
                        "quota_unit": quota_info.get("quota_info", {}).get("quota_unit"),
                        "service": quota_info.get("quota_info", {}).get("service"),
                        "consumer": quota_info.get("quota_info", {}).get("consumer"),
                        "backup_available": token_manager.has_backup_token('google_api_key'),
                        "current_api_key": self.api_key[:8] + "..." if self.api_key else None,
                        "help_links": quota_info.get("help_links", [])
                    }
                )
                
                # Also log to scraper logger for backward compatibility
                scraper_logger.warning(
                    f"Google CSE quota exceeded: {quota_info.get('error_message', 'Unknown quota error')}",
                    extra={
                        "action": "cse_quota", 
                        "status": "fail",
                        "quota_limit": quota_info.get("quota_info", {}).get("quota_limit_value"),
                        "quota_metric": quota_info.get("quota_info", {}).get("quota_metric"),
                        "backup_available": token_manager.has_backup_token('google_api_key')
                    }
                )
                raise QuotaExceededError(
                    quota_info.get("error_message", "Google CSE daily query limit has been reached"),
                    quota_info.get("quota_info"),
                    quota_info.get("help_links")
                )
            else:
                details = handle_http_error(e)
                scraper_logger.warning(
                    f"Google CSE API error: {details}",
                    extra={"action": "cse_error", "status": "fail", "status_code": e.code}
                )
                raise
        except URLError as e:
            log_url_error(e)
            raise

    def search(self, keyword: str, *, country: Optional[str], language: Optional[str], device: Optional[str], max_pages: int, results_per_page: int) -> List[Dict[str, Any]]:
        if not self.is_configured():
            raise ValueError("Google CSE is not configured")

        per_page = max(1, min(10, int(results_per_page or 10)))
        try:
            pages = int(max_pages or 3)
        except Exception:
            pages = 3
        if pages < 1 or pages > 3:
            pages = 3

        all_raw_items: List[Dict[str, Any]] = []
        total_results_fetched = 0
        
        for page_idx in range(1, pages + 1):
            start_index = ((page_idx - 1) * per_page) + 1
            params: Dict[str, Any] = {
                "key": self.api_key,
                "cx": self.cx,
                "q": keyword,
                "num": per_page,
                "start": start_index,
            }
            if config.apply_locale_hints:
                if language:
                    params["lr"] = f"lang_{language.lower()}"
                if country:
                    params["gl"] = country.lower()
            params = {k: v for k, v in params.items() if v is not None}

            data = self._get_with_cache(params)
            items = data.get("items") or []
            search_info = data.get("searchInformation", {})
            total_results = search_info.get("totalResults", "0")
            
            # Log pagination details
            scraper_logger.debug(
                f"Page {page_idx}: fetched {len(items)} items (start={start_index}, total_available={total_results})",
                extra={"action": "cse_pagination", "page": page_idx, "items_count": len(items), "start_index": start_index}
            )
            
            normalized: List[Dict[str, Any]] = []
            for idx, it in enumerate(items, start=1):
                normalized.append(map_cse_item_to_search_result(it, position=((page_idx - 1) * per_page) + idx))

            raw_item = {
                "searchQuery": {
                    "term": keyword,
                    "page": page_idx,
                },
                "searchResults": normalized,
            }
            all_raw_items.append(raw_item)
            total_results_fetched += len(items)
            
            # Break if no more items available
            if not items:
                scraper_logger.debug(f"No more items on page {page_idx}, stopping pagination")
                break
                
            # Break if we've reached the total available results
            try:
                total_available = int(total_results)
                if total_results_fetched >= total_available:
                    scraper_logger.debug(f"Reached total available results ({total_available}), stopping pagination")
                    break
            except (ValueError, TypeError):
                # If total_results is not a valid number, continue with pagination
                pass

        # Log final pagination summary
        scraper_logger.info(
            f"Pagination complete: {len(all_raw_items)} pages, {total_results_fetched} total results",
            extra={"action": "cse_pagination_summary", "pages": len(all_raw_items), "total_results": total_results_fetched}
        )

        return all_raw_items



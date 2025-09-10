from typing import List, Dict, Any, Optional, Tuple

from models import SearchConfig
from serp_tool.logging import scraper_logger
from config import config as app_config

from serp_tool.clients import GoogleCSEClient, QuotaExceededError
from serp_tool.utils import (
    _validate_and_fix_query,
    _apply_profile_sites,
    _split_query,
    _should_split_query,
    _dedup_key,
    hash_normalized_query,
)
from serp_tool.utils.delay_utils import async_delay


class GoogleSerpScraper:
    """Google SERP scraper using Google Custom Search Engine API"""

    def __init__(self):
        self.google = GoogleCSEClient()
        self._last_quota_error: Optional[QuotaExceededError] = None

    def _normalize_query(self, q: str, config: SearchConfig) -> Tuple[str, str]:
        """Normalize query for deduplication and return both cleaned and normalized versions."""
        cleaned = _validate_and_fix_query(q)
        cleaned = _apply_profile_sites(cleaned, getattr(config, 'profile_sites', None))
        normalized = ' '.join(str(cleaned).lower().split())
        return cleaned, normalized

    def normalize_query_for_dedup(self, q: str, config: SearchConfig) -> str:
        """Normalize query for deduplication purposes."""
        _, normalized = self._normalize_query(q, config)
        return normalized

    def compute_clean_and_normalized(self, q: str, config: SearchConfig) -> Tuple[str, str]:
        """Compute both cleaned and normalized versions of a query."""
        return self._normalize_query(q, config)

    @staticmethod
    def hash_normalized_query(normalized: str) -> str:
        from serp_tool.utils.dedup_utils import hash_normalized_query as _hash_normalized_query
        return _hash_normalized_query(normalized)


    async def _fetch_with_cse(self, sub_q: str, config: SearchConfig, seen: set, merged_results: List[Dict[str, Any]]) -> bool:
        try:
            scraper_logger.debug(
                "Sending request to Google CSE",
                extra={"action": "cse_request", "status": "started", "keyword": sub_q}
            )
            items = self.google.search(
                sub_q,
                country=None,
                language=None,
                device=None,
                max_pages=config.max_pages,
                results_per_page=config.results_per_page,
            )
            for item in items:
                # Process all search results in this page, not just the first one
                search_results = item.get('searchResults', [])
                for result in search_results:
                    key = _dedup_key(result)
                    if key == ("", ""):
                        # Fallback to page-based key if result is empty
                        key = (str(item.get('searchQuery', {}).get('page', '1')), str(item.get('searchQuery', {}).get('term', '')))
                    if key not in seen:
                        seen.add(key)
                        # Create a new item with just this single result
                        single_result_item = {
                            "searchQuery": item.get('searchQuery', {}),
                            "searchResults": [result]
                        }
                        merged_results.append(single_result_item)
            # Count total individual results across all pages
            total_individual_results = sum(len(item.get('searchResults', [])) for item in merged_results)
            scraper_logger.info(
                f"Fetched {len(merged_results)} page items with {total_individual_results} total results (CSE)",
                extra={"action": "result_fetch", "status": "success", "keyword": sub_q, "page_items": len(merged_results), "total_results": total_individual_results}
            )
            await async_delay()
            return True
        except QuotaExceededError as e:
            scraper_logger.error(
                f"CSE quota exceeded: {str(e)}",
                extra={
                    "action": "cse_quota", 
                    "status": "fail", 
                    "keyword": sub_q,
                    "quota_info": e.quota_info,
                    "help_links": e.help_links
                }
            )
            # Store quota error info for potential use by the job system
            self._last_quota_error = e
            raise e  # Re-raise the error since we only use Google CSE
        except Exception as e:
            scraper_logger.error(
                f"CSE failed ({e})",
                extra={"action": "cse_error", "status": "fail", "keyword": sub_q}
            )
            raise e  # Re-raise the error since we only use Google CSE
        return False


    async def scrape_keyword(self, keyword: str, config: SearchConfig) -> List[Dict[str, Any]]:
        try:
            original_input = str(keyword)
            keyword_clean = _validate_and_fix_query(keyword)
            keyword_clean = _apply_profile_sites(keyword_clean, getattr(config, 'profile_sites', None))
            scraper_logger.debug("Final query computed", extra={"action": "build_query", "status": "success", "keyword": keyword_clean})
            if original_input != keyword_clean:
                scraper_logger.debug(
                    f"Input -> Final: '{original_input}' -> '{keyword_clean}'",
                    extra={"action": "query_transform", "status": "success", "keyword": keyword_clean}
                )
            if getattr(config, 'split_long_queries', False) and _should_split_query(keyword_clean):
                sub_queries = _split_query(keyword_clean)
            else:
                sub_queries = [keyword_clean]

            merged_results: List[Dict[str, Any]] = []
            seen: set = set()

            for sub_q in sub_queries:
                before = sub_q
                sub_q = _validate_and_fix_query(sub_q)
                sub_q = _apply_profile_sites(sub_q, getattr(config, 'profile_sites', None))
                if before != sub_q:
                    scraper_logger.debug(
                        f"SubQuery cleaned: '{before}' -> '{sub_q}'",
                        extra={"action": "subquery_clean", "status": "success", "keyword": sub_q}
                    )
                
                # Only use Google CSE - check if it supports the requested features
                cse_supported = (
                    self.google.is_configured() and
                    config.include_organic and not (config.include_paa or config.include_related or config.include_ads or config.include_ai_overview)
                )

                if not cse_supported:
                    scraper_logger.warning(
                        f"Google CSE does not support requested features (PAA, related, ads, AI overview). Skipping query: {sub_q}",
                        extra={"action": "cse_unsupported", "status": "warning", "keyword": sub_q}
                    )
                    continue

                await self._fetch_with_cse(sub_q, config, seen, merged_results)

            return merged_results
        except Exception as e:
            scraper_logger.error(
                f"Error scraping keyword '{keyword}': {str(e)}",
                extra={"action": "scrape", "status": "fail", "keyword": str(keyword)}
            )
            return []

    async def scrape_keywords(self, keywords: List[str], config: SearchConfig) -> List[Dict[str, Any]]:
        all_results = []
        for keyword in keywords:
            scraper_logger.debug(
                f"Scraping keyword: {keyword}",
                extra={"action": "scrape_start", "status": "started", "keyword": str(keyword)}
            )
            results = await self.scrape_keyword(keyword, config)
            all_results.extend(results)
            await async_delay()
        return all_results



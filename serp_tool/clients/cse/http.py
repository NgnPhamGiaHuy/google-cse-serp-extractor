import json
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from serp_tool.logging import scraper_logger


def http_get_json(base_url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    url = f"{base_url}?{urlencode(params)}"
    with urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def handle_http_error(e: HTTPError) -> str:
    try:
        return e.read().decode("utf-8")
    except Exception:
        return str(e)


def parse_quota_error(error_details: str) -> Optional[Dict[str, Any]]:
    """Parse Google CSE quota error details to extract structured information."""
    try:
        error_data = json.loads(error_details)
        error_info = error_data.get("error", {})
        
        # Check if this is a quota exceeded error
        if (error_info.get("code") == 429 and 
            error_info.get("status") == "RESOURCE_EXHAUSTED" and
            any(err.get("reason") == "rateLimitExceeded" for err in error_info.get("errors", []))):
            
            # Extract quota information from details
            quota_info = {}
            for detail in error_info.get("details", []):
                if detail.get("@type") == "type.googleapis.com/google.rpc.ErrorInfo":
                    metadata = detail.get("metadata", {})
                    quota_info = {
                        "quota_limit": metadata.get("quota_limit"),
                        "quota_limit_value": metadata.get("quota_limit_value"),
                        "quota_metric": metadata.get("quota_metric"),
                        "quota_unit": metadata.get("quota_unit"),
                        "service": metadata.get("service"),
                        "consumer": metadata.get("consumer")
                    }
                    break
            
            return {
                "is_quota_error": True,
                "error_code": error_info.get("code"),
                "error_message": error_info.get("message"),
                "quota_info": quota_info,
                "help_links": [
                    link.get("url") for detail in error_info.get("details", [])
                    if detail.get("@type") == "type.googleapis.com/google.rpc.Help"
                    for link in detail.get("links", [])
                ]
            }
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


def is_quota_exceeded_error(e: HTTPError) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Check if HTTP error is a Google CSE quota exceeded error and return parsed details."""
    if e.code not in (403, 429):
        return False, None
    
    error_details = handle_http_error(e)
    quota_info = parse_quota_error(error_details)
    
    return quota_info is not None, quota_info


def log_url_error(e: URLError) -> None:
    scraper_logger.error(
        f"Google CSE network error: {e}", extra={"action": "cse_network", "status": "fail"}
    )



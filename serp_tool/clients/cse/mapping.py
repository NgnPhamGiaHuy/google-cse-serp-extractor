from typing import Dict, Any, List


def map_cse_item_to_search_result(cse_item: Dict[str, Any], position: int) -> Dict[str, Any]:
    title = cse_item.get("title") or ""
    link = cse_item.get("link") or ""
    snippet = cse_item.get("snippet") or cse_item.get("htmlSnippet") or ""
    displayed_url = cse_item.get("displayLink") or ""
    site_links = cse_item.get("pagemap", {}).get("sitelinkssearchbox", [])
    pagemap = cse_item.get("pagemap", {}) or {}
    mt_list = pagemap.get("metatags") or []
    metatags = {}
    if isinstance(mt_list, list) and mt_list:
        candidate = mt_list[0] or {}
        if isinstance(candidate, dict):
            metatags = candidate
    meta_desc_candidates: List[str] = [
        (metatags.get("og:description") or "").strip(),
        (metatags.get("twitter:description") or "").strip(),
    ]
    meta_desc_candidates = [c for c in meta_desc_candidates if c]
    if meta_desc_candidates:
        best_meta_desc = max(meta_desc_candidates, key=len)
        if ("..." in snippet) or (len(best_meta_desc) > len(snippet)):
            snippet = best_meta_desc
    return {
        "position": position,
        "title": title,
        "url": link,
        "displayedUrl": displayed_url,
        "snippet": snippet,
        "siteLinks": site_links,
        "metatags": metatags or None,
    }



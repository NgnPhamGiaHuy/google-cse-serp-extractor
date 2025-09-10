from typing import Any, Dict, List, Optional

from serp_tool.logging import scraper_logger
from schema import UnifiedItem, OrganicResult, PeopleAlsoAskItem, AdItem, empty_unified_item

from serp_tool.normalizer.helpers import (
    coerce_int,
    is_truncated,
    pick_longer_text,
    extract_followers_from_text,
)


def normalize_search_query(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the search query section for Google CSE compatibility."""
    sq = obj.get("searchQuery") or {}
    return {
        "term": sq.get("term") or obj.get("query") or obj.get("searchTerm"),
        "page": coerce_int(sq.get("page") or obj.get("page") or 1) or 1,
    }


def normalize_organic(obj: Dict[str, Any]) -> List[OrganicResult]:
    """Normalize organic results; infer connections from LinkedIn snippets/metatags."""
    records = obj.get("organicResults") or obj.get("searchResults") or []
    out: List[OrganicResult] = []
    for r in records:
        url = r.get("url") or r.get("link") or r.get("resultUrl")
        snippet = r.get("snippet") or r.get("description") or r.get("resultSnippet")
        metatags = r.get("metatags") or r.get("meta") or {}
        meta_desc_candidates = [
            (metatags.get("og:description") if isinstance(metatags, dict) else None),
            (metatags.get("twitter:description") if isinstance(metatags, dict) else None),
        ]
        best_meta_desc = pick_longer_text(*meta_desc_candidates)
        if best_meta_desc and (is_truncated(snippet) or (len(best_meta_desc) > len(str(snippet or "")))):
            snippet = best_meta_desc

        connections_text: Optional[str] = None
        connections_count: Optional[int] = None
        if url and "linkedin.com" in str(url).lower():
            for src in [best_meta_desc, (str(snippet) if snippet else None)]:
                info = extract_followers_from_text(src or "") if src else None
                if info:
                    followers_text = info.get("followersText")
                    followers_count = info.get("followersCount")
                    connections_text = followers_text
                    connections_count = followers_count
                    break

        result: OrganicResult = {
            "position": coerce_int(r.get("position") or r.get("rank")),
            "title": r.get("title") or r.get("resultTitle"),
            "url": url,
            "displayedUrl": r.get("displayedUrl") or r.get("visibleUrl"),
            "snippet": snippet,
            "siteLinks": r.get("siteLinks") or r.get("sitelinks") or [],
            "metatags": metatags or None,
            "connectionsText": connections_text,
            "connectionsCount": connections_count,
        }
        if connections_text is not None:
            result["connections_text"] = connections_text  # type: ignore
        if connections_count is not None:
            result["connections_count"] = connections_count  # type: ignore
        out.append(result)
    return out


def normalize_paa(obj: Dict[str, Any]) -> List[PeopleAlsoAskItem]:
    paa = obj.get("peopleAlsoAsk") or obj.get("paa") or []
    out: List[PeopleAlsoAskItem] = []
    for p in paa:
        out.append({
            "question": p.get("question"),
            "answer": p.get("answer"),
            "url": p.get("url"),
        })
    return out


def normalize_related(obj: Dict[str, Any]) -> List[Any]:
    related = obj.get("relatedSearches") or obj.get("relatedQueries") or []
    return related


def normalize_ads(obj: Dict[str, Any]) -> List[AdItem]:
    ads = obj.get("ads") or obj.get("paidResults") or []
    out: List[AdItem] = []
    for ad in ads:
        out.append({
            "position": coerce_int(ad.get("position")),
            "title": ad.get("title"),
            "url": ad.get("url") or ad.get("link"),
            "advertiser": ad.get("advertiser") or ad.get("source"),
            "snippet": ad.get("description") or ad.get("snippet"),
        })
    return out


def normalize_ai_overview(obj: Dict[str, Any]) -> Optional[Any]:
    return obj.get("aiOverview") or obj.get("ai_overview")


def normalize_item(raw: Dict[str, Any]) -> UnifiedItem:
    """Normalize a raw item into the unified schema.

    Preserves logging and error handling from the original implementation.
    """
    try:
        unified: UnifiedItem = empty_unified_item()
        unified["searchQuery"] = normalize_search_query(raw)
        unified["organicResults"] = normalize_organic(raw)
        unified["peopleAlsoAsk"] = normalize_paa(raw)
        unified["relatedSearches"] = normalize_related(raw)
        unified["ads"] = normalize_ads(raw)
        unified["aiOverview"] = normalize_ai_overview(raw)

        if not unified["organicResults"]:
            scraper_logger.debug(
                "Normalization: no organic results on item",
                extra={"action": "normalize", "status": "warn"}
            )
        return unified
    except Exception as e:
        scraper_logger.error(
            f"Normalization failed: {e}", extra={"action": "normalize", "status": "fail"}
        )
        return empty_unified_item()


def normalize_items(raw_items: List[Dict[str, Any]]) -> List[UnifiedItem]:
    """Normalize a list of raw items into unified schema items."""
    return [normalize_item(it) for it in (raw_items or [])]



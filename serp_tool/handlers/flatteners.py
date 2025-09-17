import json
from datetime import datetime
from typing import Any, Dict, List

from serp_tool.handlers.followers import _extract_followers_from_record


def _flatten_common(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common fields shared by all flattened rows."""
    sq = item.get('searchQuery') or {}
    term = sq.get('term') or item.get('query') or item.get('searchTerm') or ''
    page = sq.get('page') or item.get('page') or 1
    fetched_at = item.get('fetchedAt') or item.get('createdAt') or datetime.utcnow().isoformat()
    return {
        'query': term,
        'page': page,
        'fetched_at': fetched_at,
    }


def _flatten_organic(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten organic results into row dictionaries."""
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        common = _flatten_common(item)
        organic = item.get('organicResults') or item.get('searchResults') or []
        for r in organic:
            connections_text = r.get('connectionsText') or r.get('connections_text')
            connections_count = r.get('connectionsCount') or r.get('connections_count')
            if connections_text is None and connections_count is None:
                inferred_text, inferred_count = _extract_followers_from_record(r)
                connections_text = inferred_text
                connections_count = inferred_count
            rows.append({
                **common,
                'position': r.get('position') or r.get('rank') or '',
                'title': r.get('title') or r.get('resultTitle') or '',
                'url': r.get('url') or r.get('link') or '',
                'displayed_url': r.get('displayedUrl') or r.get('visibleUrl') or '',
                'snippet': r.get('snippet') or r.get('description') or '',
                'connections_text': connections_text,
                'connections_count': connections_count,
            })
    return rows


def _flatten_paa(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten People Also Ask entries."""
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        common = _flatten_common(item)
        paa = item.get('peopleAlsoAsk') or item.get('paa') or []
        for p in paa:
            rows.append({
                **common,
                'question': p.get('question') or '',
                'answer': p.get('answer') or '',
                'url': p.get('url') or ''
            })
    return rows


def _flatten_related(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten related queries into row dictionaries."""
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        common = _flatten_common(item)
        related = item.get('relatedQueries') or item.get('relatedSearches') or []
        for rq in related:
            q = rq.get('query') if isinstance(rq, dict) else rq
            rows.append({ **common, 'related_query': q or '' })
    return rows


def _flatten_paid(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten paid ad results into row dictionaries."""
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        common = _flatten_common(item)
        ads = item.get('ads') or item.get('paidResults') or []
        for ad in ads:
            rows.append({
                **common,
                'position': ad.get('position') or '',
                'title': ad.get('title') or '',
                'url': ad.get('url') or ad.get('link') or '',
                'advertiser': ad.get('advertiser') or ad.get('source') or '',
                'snippet': ad.get('description') or ad.get('snippet') or ''
            })
    return rows


def _flatten_ai_overview(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten AI overview content as JSON strings."""
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        common = _flatten_common(item)
        ai = item.get('aiOverview') or item.get('ai_overview') or None
        if ai is None:
            continue
        rows.append({ **common, 'content_json': json.dumps(ai, ensure_ascii=False) })
    return rows



from typing import List, Optional


def _ensure_quoted(value: str) -> str:
    """Return value wrapped in quotes if it has whitespace and is not already quoted."""
    s = str(value).strip()
    if not s:
        return s
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s
    if ' ' in s:
        return f'"{s}"'
    return s


def _build_site_filter(existing_query: str, profile_sites: Optional[List[str]] = None) -> str:
    """Build the site filter suffix that `_apply_profile_sites` would append.

    Returns only the appended portion, or an empty string when nothing changes.
    """
    from serp_tool.utils.query_utils import _apply_profile_sites

    if not profile_sites or len(profile_sites) == 0:
        return ''

    full_query = _apply_profile_sites(existing_query, profile_sites)

    if full_query == existing_query:
        return ''

    site_filter_part = full_query[len(existing_query):].strip()
    return site_filter_part


def _tokenize_roles(values: List[str]) -> List[str]:
    """Split role strings on commas and ORs, returning unique, order-preserving tokens."""
    tokens: List[str] = []
    for v in values:
        if not v:
            continue
        s = str(v)
        tmp = s.replace(';', ',')
        for segment in tmp.split(','):
            segment = segment.strip()
            if not segment:
                continue
            subparts = [p.strip() for p in segment.split(' OR ')]
            if len(subparts) == 1 and ' or ' in segment.lower():
                subparts = [p.strip() for p in segment.split(' or ')]
            for p in subparts:
                if p:
                    tokens.append(p)
    seen = set()
    unique_tokens: List[str] = []
    for t in tokens:
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        unique_tokens.append(t)
    return unique_tokens


def _compose_query(anchor: str, role_values: List[str], profile_sites: Optional[List[str]] = None) -> str:
    """Compose a base query: anchor + optional site filter + optional role OR expression."""
    anchor_part = _ensure_quoted(anchor)
    roles = _tokenize_roles(role_values)
    role_expr = ''
    if roles:
        normalized_roles = [_ensure_quoted(r) for r in roles]
        role_expr = " (" + " OR ".join(normalized_roles) + ")"
    base_query = anchor_part + _build_site_filter(anchor_part, profile_sites) + role_expr
    return base_query.strip()



import math
import re
from typing import List, Optional


def _should_split_query(query: str) -> bool:
    """Heuristic for splitting overly long queries into sub-queries."""
    tokens = [t for t in str(query).split() if t]
    return len(query) > 256 or len(tokens) > 14


def _split_query(query: str) -> List[str]:
    """Split a long query into 3-6 chunks of roughly even length by tokens."""
    tokens = [t for t in str(query).split() if t]
    if not tokens:
        return []
    approx_tokens_per_chunk = 8
    desired_chunks = math.ceil(len(tokens) / approx_tokens_per_chunk)
    num_chunks = max(3, min(6, desired_chunks))
    chunk_size = math.ceil(len(tokens) / num_chunks)
    sub_queries: List[str] = []
    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i + chunk_size]
        if chunk:
            sub_queries.append(" ".join(chunk))
    return sub_queries[:6]


def _validate_and_fix_query(q: str) -> str:
    """Normalize whitespace, balance parentheses, and clean redundant operators."""
    query = str(q or '').strip()
    if not query:
        return ''
    query = ' '.join(query.split())
    query = re.sub(r'\(\s*(?:OR|AND)\s+', '(', query, flags=re.IGNORECASE)
    query = re.sub(r'\s+(?:OR|AND)\s*\)', ')', query, flags=re.IGNORECASE)
    query = re.sub(r'\b(OR|AND)\b(?:\s+\b(OR|AND)\b)+', r'\1', query, flags=re.IGNORECASE)
    query = re.sub(r'(?:\s+\b(?:OR|AND)\b)+\s*$', '', query, flags=re.IGNORECASE)
    query = re.sub(r'^\s*\b(?:OR|AND)\b\s+', '', query, flags=re.IGNORECASE)
    prev = None
    while prev != query:
        prev = query
        query = re.sub(r'\(\s*\)', '', query)
        query = query.replace('( )', '').replace('()', '')
    balanced_chars = []
    open_count = 0
    for ch in query:
        if ch == '(':
            open_count += 1
            balanced_chars.append(ch)
        elif ch == ')':
            if open_count > 0:
                open_count -= 1
                balanced_chars.append(ch)
            else:
                continue
        else:
            balanced_chars.append(ch)
    if open_count > 0:
        balanced_chars.append(')' * open_count)
    query = ''.join(balanced_chars)
    query = ' '.join(query.split())
    return query


def _apply_profile_sites(query: str, profile_sites: Optional[List[str]]) -> str:
    """Append site filters if not already present in the query."""
    if not query:
        return query

    if not profile_sites or len(profile_sites) == 0:
        return query

    ql = query.lower()

    valid_sites = [s for s in profile_sites if s and s.strip() and s.startswith('site:')]

    if not valid_sites:
        return query

    domains = [s.split(':', 1)[1] for s in valid_sites if ':' in s]
    if any(domain in ql for domain in domains):
        return query

    return f"{query} (" + " OR ".join(valid_sites) + ")"


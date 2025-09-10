import hashlib
from typing import Any, Dict, Tuple


def _dedup_key(item: Dict[str, Any]) -> Tuple[str, str]:
    url = (
        item.get('url') or
        item.get('resultUrl') or
        item.get('link') or
        ''
    )
    title = (
        item.get('title') or
        item.get('resultTitle') or
        ''
    )
    return str(title), str(url)


def hash_normalized_query(normalized: str) -> str:
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()



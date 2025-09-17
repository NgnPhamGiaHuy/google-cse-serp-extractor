import hashlib
import json
import time

from pathlib import Path
from typing import Any, Dict, Optional


def build_cache_key(cache_dir: Path, params: Dict[str, Any]) -> Path:
    payload = json.dumps(params, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.json"


def read_cache(path: Path, ttl_seconds: int) -> Optional[Dict[str, Any]]:
    now = int(time.time())
    if path.exists():
        try:
            mtime = int(path.stat().st_mtime)
            if now - mtime <= ttl_seconds:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return None
    return None


def write_cache(path: Path, data: Dict[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


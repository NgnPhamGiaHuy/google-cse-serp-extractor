from typing import Any, Dict, Optional
import re


def coerce_int(value: Any) -> Optional[int]:
    """Best-effort convert a value to int; returns None on failure."""
    try:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


def is_truncated(text: Optional[str]) -> bool:
    """Heuristic to detect truncated snippets (ellipsis or missing terminal punctuation)."""
    if not text:
        return False
    t = str(text).strip()
    return "..." in t or (len(t) > 0 and t[-1] not in ".!?…")


def pick_longer_text(*candidates: Optional[str]) -> Optional[str]:
    """Return the longest non-empty trimmed candidate string, or None."""
    texts = [str(c).strip() for c in candidates if c and str(c).strip()]
    if not texts:
        return None
    return max(texts, key=len)


def extract_followers_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Parse a text for followers/connections label and count across locales.

    Returns dict with keys 'followersText' and 'followersCount' or None.
    """
    try:
        if not text:
            return None
        follower_terms = [
            "followers", "connections",
            "kết nối", "người theo dõi",
            "seguidores", "conexiones", "conexões",
            "abonnés", "relations",
            "follower", "kontakte",
            "follower", "connessioni",
            "pengikut", "koneksi",
            "takipçi", "bağlantı",
            "ผู้ติดตาม", "การเชื่อมต่อ",
            "フォロワー", "つながり",
            "팔로워", "연결",
            "关注者", "人脉",
        ]
        terms_alt = "|".join(sorted({re.escape(t) for t in follower_terms}, key=len, reverse=True))
        num_alt = r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?\s*[kKmM]?\+?)"
        patterns = [
            rf"{num_alt}\s*(?:{terms_alt})",
            rf"(?:{terms_alt})\s*[:：]?\s*{num_alt}",
        ]
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if not m:
                continue
            num_str = m.group(1) if m.group(1) else m.group(0)
            followers_text = m.group(0).strip()
            num = None
            s = num_str.replace(',', '').replace(' ', '')
            k_match = re.fullmatch(r"(\d+(?:\.\d+)?)[kK]\+?", s)
            m_match = re.fullmatch(r"(\d+(?:\.\d+)?)[mM]\+?", s)
            if k_match:
                num = int(float(k_match.group(1)) * 1000)
            elif m_match:
                num = int(float(m_match.group(1)) * 1_000_000)
            else:
                s = s.rstrip('+').replace('.', '')
                try:
                    num = int(float(s))
                except Exception:
                    num = None
            return {"followersText": followers_text, "followersCount": num}
        return None
    except Exception:
        return None



import re
from typing import Any, Dict, List, Optional, Tuple
from serp_tool.logging import files_logger


def _followers_label_regexes() -> List[re.Pattern]:
    words = [
        r"followers?", r"connections?",
        r"người\s+theo\s+dõi", r"kết\s+nối",
        r"seguidores?", r"conexiones?", r"conexões",
        r"abonnés?", r"relations?",
        r"abonnenten", r"kontakte",
        r"seguaci", r"connessioni",
        r"pengikut", r"koneksi",
        r"takipçi", r"bağlantı",
        r"ผู้ติดตาม", r"การเชื่อมต่อ",
        r"フォロワー", r"つながり",
        r"팔로워", r"연결",
        r"关注者", r"人脉",
    ]
    num = r"(?P<num>\d{1,3}(?:[\s.,]\d{3})+|\d+(?:[\.,]\d+)?)"
    suf = r"(?P<suf>[KkMmBb]?)"
    plus = r"\+?"
    sep = r"[\s\u00A0]*"
    word_group = r"(?:" + "|".join(words) + r")"
    patterns = [
        re.compile(rf"{num}{sep}{suf}{sep}{plus}{sep}{word_group}\b", re.IGNORECASE),
        re.compile(rf"{num}{sep}{word_group}\b", re.IGNORECASE),
        re.compile(rf"\b{word_group}{sep}{num}{sep}{suf}{sep}{plus}?", re.IGNORECASE),
    ]
    return patterns


def _normalize_human_number(num_str: Optional[str], suffix: str) -> Optional[int]:
    if not num_str:
        return None
    try:
        s = str(num_str).strip()
        s = s.replace('\u202F', ' ').replace('\u00A0', ' ')
        s = s.replace(' ', '')
        if ',' in s and '.' in s:
            s = s.replace(',', '')
        else:
            if ',' in s:
                s = s.replace(',', '.')
        value = float(s)
        mult = 1
        suf = (suffix or '').lower()
        if suf == 'k':
            mult = 1000
        elif suf == 'm':
            mult = 1000000
        elif suf == 'b':
            mult = 1000000000
        return int(round(value * mult))
    except Exception:
        return None


def _extract_followers_from_record(record: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
    """Extract a followers label and normalized count from a result record if present."""
    try:
        candidates: List[str] = []

        def _collect_strings(value: Any) -> None:
            if isinstance(value, str):
                s = value.strip()
                if s:
                    candidates.append(s)
            elif isinstance(value, list):
                for v in value:
                    _collect_strings(v)
            elif isinstance(value, dict):
                for v in value.values():
                    _collect_strings(v)

        for key in ['snippet', 'description', 'title', 'displayedUrl', 'visibleUrl', 'richSnippet', 'inline']:
            if key in record:
                _collect_strings(record.get(key))
        _collect_strings(record)

        followers_patterns = _followers_label_regexes()
        for text in candidates:
            for regex in followers_patterns:
                m = regex.search(text)
                if not m:
                    continue
                original = m.group(0).strip()
                number_part = m.group('num') if 'num' in m.groupdict() else None
                suffix = m.group('suf') if 'suf' in m.groupdict() else ''
                normalized = _normalize_human_number(number_part, suffix)
                if normalized is None:
                    try:
                        files_logger.warning(
                            f"Followers parse failed for '{original}'",
                            extra={"action": "followers_parse", "status": "warn"}
                        )
                    except Exception:
                        pass
                return original, normalized
    except Exception:
        try:
            files_logger.warning(
                "Followers extraction error; continuing without followers",
                extra={"action": "followers_extract", "status": "warn"}
            )
        except Exception:
            pass
    return None, None



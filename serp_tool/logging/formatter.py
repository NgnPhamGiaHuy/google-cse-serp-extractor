import logging
from datetime import datetime
from pathlib import Path

from .filters import ContextDefaultsFilter

_log_directory = Path("logs")
_log_directory.mkdir(exist_ok=True)


def build_formatter() -> logging.Formatter:
    """Create the standard formatter used across file and console handlers."""
    fmt = (
        "%(asctime)s | %(levelname)s | %(name)s | "
        "query_id=%(query_id)s | keyword=%(keyword)s | "
        "action=%(action)s | status=%(status)s | %(message)s"
    )
    datefmt = "%Y-%m-%d %H:%M:%S"
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def current_log_file() -> Path:
    """Return today's rotating log file path (app_YYYYMMDD.log)."""
    ts = datetime.now().strftime("%Y%m%d")
    return _log_directory / f"app_{ts}.log"



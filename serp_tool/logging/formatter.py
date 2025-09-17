import json
import logging
from datetime import datetime
from pathlib import Path

from .filters import ContextDefaultsFilter

_log_directory = Path("logs")
_log_directory.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }


        for key in ("query_id", "keyword", "action", "status", "page", "items_count", "start_index", "results_per_page", "max_pages", "pages", "total_results", "requested_max_pages"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)


        for key, value in record.__dict__.items():
            if key not in payload and key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module",
                "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName", "process", "asctime"
            ):

                try:
                    json.dumps(value)
                    payload[key] = value
                except Exception:
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


def build_formatter() -> logging.Formatter:
    return JSONFormatter()


def current_log_file() -> Path:
    ts = datetime.now().strftime("%Y%m%d")
    return _log_directory / f"app_{ts}.log"



from .filters import ContextDefaultsFilter
from .formatter import build_formatter, current_log_file
from .queueing import ensure_queue_listener
from .adapter import ContextLoggerAdapter
from .core import setup_root_logging, get_logger, get_quota_logger

# Pre-created loggers matching previous module-level convenience loggers
app_logger = get_logger("app")
scraper_logger = get_logger("scraper")
files_logger = get_logger("files")
cli_logger = get_logger("cli")

__all__ = [
    "ContextDefaultsFilter",
    "build_formatter",
    "current_log_file",
    "ensure_queue_listener",
    "ContextLoggerAdapter",
    "setup_root_logging",
    "get_logger",
    "get_quota_logger",
    "app_logger",
    "scraper_logger",
    "files_logger",
    "cli_logger",
]



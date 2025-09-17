import logging
from typing import Optional, Dict, Any

from config import config

from .queueing import ensure_queue_listener, build_queue_handler
from .formatter import build_formatter
from .filters import ContextDefaultsFilter
from .adapter import ContextLoggerAdapter


def setup_root_logging() -> None:
    if getattr(setup_root_logging, "_initialized", False):
        return

    level = getattr(logging, config.log_level, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    listener = ensure_queue_listener()
    qh = build_queue_handler(level)
    root_logger.handlers.clear()
    root_logger.addHandler(qh)

    if config.debug:
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(build_formatter())
        console.addFilter(ContextDefaultsFilter())
        root_logger.addHandler(console)

    setup_root_logging._initialized = True


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> ContextLoggerAdapter:
    setup_root_logging()
    base_logger = logging.getLogger(name)
    return ContextLoggerAdapter(base_logger, context or {})


def get_quota_logger() -> ContextLoggerAdapter:
    return get_logger("quota", {
        "action": "quota_monitoring",
        "component": "quota_manager"
    })



import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener

from .formatter import build_formatter, current_log_file
from .filters import ContextDefaultsFilter

_log_queue_listener: QueueListener | None = None
_log_queue = None


def create_file_handler() -> logging.Handler:
    """Create the rotating file handler with our formatter and default context filter."""
    handler = TimedRotatingFileHandler(
        filename=str(current_log_file()), when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    handler.setFormatter(build_formatter())
    handler.addFilter(ContextDefaultsFilter())
    return handler


def ensure_queue_listener() -> QueueListener:
    """Create and start a singleton QueueListener feeding the rotating file handler."""
    from queue import Queue
    global _log_queue_listener, _log_queue
    if _log_queue_listener is not None:
        return _log_queue_listener
    file_handler = create_file_handler()
    _log_queue = Queue(maxsize=10000)
    _log_queue_listener = QueueListener(_log_queue, file_handler)
    _log_queue_listener.start()
    return _log_queue_listener


def build_queue_handler(level: int) -> QueueHandler:
    """Build a QueueHandler that writes to the same queue used by the listener."""
    global _log_queue
    qh = QueueHandler(_log_queue)
    qh.setLevel(level)
    return qh



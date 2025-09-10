import logging


class ContextDefaultsFilter(logging.Filter):
    """Ensure expected context fields exist on every LogRecord to avoid KeyError in formatter."""
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("query_id", "keyword", "action", "status"):
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True



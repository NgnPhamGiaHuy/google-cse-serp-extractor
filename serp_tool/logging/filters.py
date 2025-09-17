import logging


class ContextDefaultsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("query_id", "keyword", "action", "status"):
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True



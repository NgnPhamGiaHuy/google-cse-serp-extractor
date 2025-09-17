import logging
from typing import Dict, Any


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy() if self.extra else {}
        provided = kwargs.get("extra") or {}
        extra.update({
            "query_id": "-",
            "keyword": "-",
            "action": "-",
            "status": "-",
        })
        extra.update({k: v for k, v in provided.items() if v is not None})
        kwargs["extra"] = extra
        return msg, kwargs



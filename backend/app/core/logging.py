import json
import logging
import sys
from datetime import datetime, timezone


class RequestLogFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "method": getattr(record, "method", None),
            "route": getattr(record, "route", None),
            "status": getattr(record, "status", None),
            "duration_ms": getattr(record, "duration_ms", None),
        })


def configure_request_logging(level):
    logger = logging.getLogger("skillsync.requests")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(RequestLogFormatter())
        logger.addHandler(handler)
    return logger

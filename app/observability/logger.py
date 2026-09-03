import json
import logging
import time
import uuid
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Structured JSON & Console logger for AI Agent observability.
    Captures trace IDs, timestamps, log levels, operation names, and contextual fields.
    """

    def __init__(self, name: str = "AIAgent"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @staticmethod
    def generate_trace_id() -> str:
        return str(uuid.uuid4())[:8]

    def _format_event(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": level,
            "message": message,
            "trace_id": trace_id or "N/A"
        }
        if duration_ms is not None:
            payload["duration_ms"] = round(duration_ms, 2)
        if extra:
            payload.update(extra)
        return json.dumps(payload)

    def info(self, message: str, trace_id: Optional[str] = None, duration_ms: Optional[float] = None, **kwargs):
        event_str = self._format_event("INFO", message, trace_id, duration_ms, kwargs)
        self.logger.info(event_str)

    def warning(self, message: str, trace_id: Optional[str] = None, duration_ms: Optional[float] = None, **kwargs):
        event_str = self._format_event("WARNING", message, trace_id, duration_ms, kwargs)
        self.logger.warning(event_str)

    def error(self, message: str, trace_id: Optional[str] = None, duration_ms: Optional[float] = None, **kwargs):
        event_str = self._format_event("ERROR", message, trace_id, duration_ms, kwargs)
        self.logger.error(event_str)

    def debug(self, message: str, trace_id: Optional[str] = None, duration_ms: Optional[float] = None, **kwargs):
        event_str = self._format_event("DEBUG", message, trace_id, duration_ms, kwargs)
        self.logger.debug(event_str)


# Global default logger instance
logger = StructuredLogger()

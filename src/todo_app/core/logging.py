"""Structured (JSON) logging.

``configure_logging`` installs a JSON formatter on the root logger so every
record — including the ``extra={...}`` fields emitted by the request middleware
and the use cases — serializes as one JSON object per line, ready for a log
pipeline. ``get_logger`` is the helper classes use to obtain a named logger;
classes constructor-inject it (defaulting to ``get_logger(__name__)``) so it can
be swapped in tests.
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Standard LogRecord attributes — everything else on the record came from an
# ``extra={...}`` and is merged into the JSON payload.
_RESERVED = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Render a log record (plus its structured ``extra`` fields) as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON handler on the root logger at the given level."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (the injection seam for classes that log)."""
    return logging.getLogger(name)

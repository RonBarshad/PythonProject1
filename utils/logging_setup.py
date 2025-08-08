from __future__ import annotations

import logging
import os
import sys
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger
except Exception:  # pragma: no cover
    jsonlogger = None  # type: ignore


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a JSON formatter and stdout handler.

    Safe to call multiple times – handlers are reset.
    """
    root = logging.getLogger()
    # Clear any existing handlers to avoid duplicate logs
    for h in list(root.handlers):
        root.removeHandler(h)
    # Allow override via env var LOG_LEVEL (e.g., DEBUG, INFO, WARNING)
    env_level = os.getenv("LOG_LEVEL")
    if env_level:
        try:
            level = getattr(logging, env_level.upper(), level)
        except Exception:
            pass
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if jsonlogger is not None:
        fmt = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s '
            '%(request_id)s %(user_id)s %(username)s %(telegram_id)s %(app_user_id)s '
            '%(handler)s %(ticker)s %(op)s %(table)s %(duration_ms)s'
        )
        handler.setFormatter(fmt)
    else:  # fallback to plain text
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s: %(message)s')
        handler.setFormatter(formatter)
    root.addHandler(handler)



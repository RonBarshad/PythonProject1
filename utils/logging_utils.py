from __future__ import annotations

import time
import functools
import inspect
import logging

logger = logging.getLogger(__name__)


def log_call(name: str):
    """Decorator to log start/finish/duration for async or sync callables."""
    def deco(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                logger.info("start", extra={"handler": name})
                try:
                    result = await fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000
                    logger.info("ok", extra={"handler": name, "duration_ms": round(duration_ms, 2)})
                    return result
                except Exception:
                    duration_ms = (time.perf_counter() - start) * 1000
                    logger.exception("error", extra={"handler": name, "duration_ms": round(duration_ms, 2)})
                    raise
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                logger.info("start", extra={"handler": name})
                try:
                    result = fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000
                    logger.info("ok", extra={"handler": name, "duration_ms": round(duration_ms, 2)})
                    return result
                except Exception:
                    duration_ms = (time.perf_counter() - start) * 1000
                    logger.exception("error", extra={"handler": name, "duration_ms": round(duration_ms, 2)})
                    raise
            return sync_wrapper
    return deco



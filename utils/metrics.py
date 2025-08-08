from __future__ import annotations

import logging
from typing import Optional

try:
    from prometheus_client import Counter, Histogram, start_http_server
except Exception:  # pragma: no cover
    # Fallback dummies
    class Counter:  # type: ignore
        def __init__(self, *a, **k):
            pass
        def labels(self, **k):
            return self
        def inc(self, v: float = 1.0):
            pass
    class Histogram:  # type: ignore
        def __init__(self, *a, **k):
            pass
        def labels(self, **k):
            return self
        def observe(self, v: float):
            pass
    def start_http_server(port: int):
        pass

logger = logging.getLogger(__name__)

# Common metrics
handler_calls = Counter(
    'telegram_handler_calls_total', 'Telegram handler calls', ['handler']
)
handler_duration = Histogram(
    'telegram_handler_duration_ms', 'Telegram handler duration (ms)', ['handler']
)
db_queries = Counter(
    'db_queries_total', 'Database queries', ['op', 'table']
)
db_duration = Histogram(
    'db_query_duration_ms', 'Database query duration (ms)', ['op', 'table']
)
api_calls = Counter(
    'external_api_calls_total', 'External API calls', ['service', 'op']
)
api_duration = Histogram(
    'external_api_duration_ms', 'External API duration (ms)', ['service', 'op']
)


def start_metrics_server(port: int = 9100) -> None:
    try:
        start_http_server(port)
        logger.info("Prometheus metrics server started", extra={"handler": "metrics", "port": port})
    except Exception as exc:
        logger.error("Failed to start metrics server: %s", exc)



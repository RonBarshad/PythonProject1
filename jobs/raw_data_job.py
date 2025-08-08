"""
jobs/raw_data_job.py
Mission: Run the raw-data ingestion once per day at a specific UTC time, independent of the bot.

This containerized job loops forever and triggers `main.run_raw_data_only()` once per
calendar day at the configured time.

Configuration via environment variables:
- LOG_LEVEL          → standard logging level (INFO, DEBUG, ...)
- RAW_DATA_UTC_TIME  → HH:MM in 24h format, default "06:00"
- RUN_ON_STARTUP     → if "true", execute a run immediately on startup (default: false)
"""

from __future__ import annotations

import os
import time
from datetime import datetime, date, timezone
import logging

from utils.logging_setup import setup_logging


def _get_env_time() -> str:
    value = os.getenv("RAW_DATA_UTC_TIME", "06:00").strip()
    # Basic validation HH:MM
    try:
        hour_str, minute_str = value.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except Exception:
        value = "06:00"
    return value


def _should_run_now(target_hhmm: str, last_run_utc_date: date | None) -> bool:
    now_utc = datetime.now(timezone.utc)
    hhmm_now = now_utc.strftime("%H:%M")
    # ensure we run only once per UTC day
    if hhmm_now == target_hhmm:
        if last_run_utc_date != now_utc.date():
            return True
    return False


def _run_once(logger: logging.Logger) -> None:
    try:
        logger.info("raw_data_job: starting run_raw_data_only()")
        # Import lazily to avoid heavy imports at container start
        from main import run_raw_data_only  # type: ignore
        run_raw_data_only()
        logger.info("raw_data_job: run_raw_data_only() finished successfully")
    except Exception as exc:
        logger.exception("raw_data_job: run failed: %s", exc)


def main() -> None:
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("raw_data_job: initialized")

    target_hhmm = _get_env_time()
    logger.info("raw_data_job: configured UTC run time = %s", target_hhmm)

    last_run_utc_date: date | None = None

    run_on_startup = os.getenv("RUN_ON_STARTUP", "false").lower() == "true"
    if run_on_startup:
        _run_once(logger)
        last_run_utc_date = datetime.now(timezone.utc).date()

    # Simple loop, check every 30 seconds
    while True:
        try:
            if _should_run_now(target_hhmm, last_run_utc_date):
                _run_once(logger)
                last_run_utc_date = datetime.now(timezone.utc).date()
        except Exception as loop_exc:
            logger.exception("raw_data_job: loop error: %s", loop_exc)
        time.sleep(30)


if __name__ == "__main__":
    main()



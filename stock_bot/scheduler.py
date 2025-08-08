"""
stock_bot/scheduler.py
Independent scheduler service for daily data ingestion and AI analysis.

Runs two daily jobs using APScheduler's BlockingScheduler:
  - 05:00: Insert/refresh raw data for all tickers
  - 06:00: Run self-AI daily analysis for all tickers (for yesterday) and refresh cache

Designed to run as a separate Docker service so it doesn't depend on the bot process.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.config import get
from utils.logging_setup import setup_logging
from stock_bot import cache

# Use existing modules for work
import ai.analysis_runner as ai_runner
import ai.self_ai_analysis_by_ticker as self_ai_analysis_by_ticker


def job_run_raw_data() -> None:
    logger = logging.getLogger(__name__)
    try:
        tickers = get("tickers") or []
        if not tickers:
            logger.warning("No tickers configured; skipping raw data job")
            return
        ai_runner.insert_raw_data_only(tickers)
        logger.info("Daily raw data ingestion completed", extra={"handler": "job_run_raw_data"})
    except Exception as exc:
        logger.exception("Daily raw data ingestion failed: %s", exc, extra={"handler": "job_run_raw_data"})


def job_run_daily_self_ai() -> None:
    logger = logging.getLogger(__name__)
    try:
        tickers = get("tickers") or []
        model = get("self_analysis.model")
        if not tickers:
            logger.warning("No tickers configured; skipping self-AI job")
            return
        for t in tickers:
            self_ai_analysis_by_ticker.self_ai_analysis_by_ticker(
                analysis_event_date=date.today() - timedelta(days=1),
                company_ticker=t,
                model=model,
                weights="",
                analysis_type="day",
                test="no",
                test_name="production",
            )
        # Refresh cache to reflect new data
        try:
            cache.get_cached_yesterdays_analysis(force=True)
        except Exception:
            pass
        logger.info("Daily self-AI analysis completed", extra={"handler": "job_run_daily_self_ai"})
    except Exception as exc:
        logger.exception("Daily self-AI analysis failed: %s", exc, extra={"handler": "job_run_daily_self_ai"})


def main() -> None:
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting scheduler service", extra={"handler": "scheduler_init"})

    # You can control timezone via container TZ env var if needed
    scheduler = BlockingScheduler()

    # 05:00 daily – raw data
    scheduler.add_job(job_run_raw_data, CronTrigger(hour=5, minute=0), id="raw_data_ingest", replace_existing=True)
    # 06:00 daily – self AI
    scheduler.add_job(job_run_daily_self_ai, CronTrigger(hour=6, minute=0), id="daily_self_ai", replace_existing=True)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()



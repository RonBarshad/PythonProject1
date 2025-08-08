"""
stock_bot/mailer.py
Independent mailer service to send daily stock analysis emails with charts.

Uses APScheduler to run once per day at a configured time. Pulls recipients
from a simple config list or (future) from DB, generates charts, and sends mail.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.config import get
from utils.logging_setup import setup_logging
from notifications.email_sender import send_stock_analysis_email_with_charts


def _get_recipients() -> List[str]:
    # Placeholder: use a config list; can be replaced with DB query later
    recipients = get("email.recipients") or []
    if isinstance(recipients, str):
        recipients = [recipients]
    return [r for r in recipients if isinstance(r, str) and r.strip()]


def job_send_daily_emails() -> None:
    logger = logging.getLogger(__name__)
    try:
        recipients = _get_recipients()
        if not recipients:
            logger.info("No email recipients configured; skipping daily mail job")
            return
        days = int(get("email.days") or 60)
        for r in recipients:
            ok = send_stock_analysis_email_with_charts(r, days=days)
            logger.info(
                "email_sent" if ok else "email_failed",
                extra={"handler": "job_send_daily_emails", "recipient": r, "days": days},
            )
    except Exception as exc:
        logger.exception("Daily mail job failed: %s", exc, extra={"handler": "job_send_daily_emails"})


def main() -> None:
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting mailer service", extra={"handler": "mailer_init"})

    scheduler = BlockingScheduler()
    # Default 07:00 daily – configurable via config if needed later
    hour = int(get("email.hour") or 7)
    minute = int(get("email.minute") or 0)
    scheduler.add_job(job_send_daily_emails, CronTrigger(hour=hour, minute=minute), id="daily_mail", replace_existing=True)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Mailer stopped")


if __name__ == "__main__":
    main()



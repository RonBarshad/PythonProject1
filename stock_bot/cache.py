"""In-memory caches and buffers for the stock_bot runtime.

Contains:
1. Daily cache for yesterday's AI analysis
2. Daily/all-users data cache
3. Event buffer for bulk-inserting `fact_telegram_bot_actions`
"""

from __future__ import annotations

from datetime import date, timedelta, datetime
from typing import Optional, Dict, Any, List
import logging
import pandas as pd
from stock_bot.db_data_handaling import get_all_users_data  # imported late to avoid cycle
from config.config import get
from stock_bot.db_data_handaling import (
    get_yesterdays_ai_analysis,
    insert_bot_actions,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Yesterday's AI analysis (daily cache)
# ---------------------------------------------------------------------------

_YESTERDAYS_ANALYSIS: Optional[pd.DataFrame] = None
_LAST_REFRESH: Optional[date] = None  # The *yesterday* date this cache represents

# ---------------------------------------------------------------------------
# Users-data cache (on-demand)
# ---------------------------------------------------------------------------

_USERS_DATA: Optional[pd.DataFrame] = None

# ---------------------------------------------------------------------------
# Event buffer for fact_telegram_bot_actions (batch insert)
# ---------------------------------------------------------------------------

_EVENT_BUFFER: List[Dict[str, Any]] = []
_EVENT_BATCH_SIZE = 10        # flush when this many events collected
_EVENT_FLUSH_SECONDS = 300    # or after 5 minutes
_LAST_EVENT_FLUSH: Optional[datetime] = None

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _needs_refresh() -> bool:
    yesterday = date.today() - timedelta(days=1)
    return _LAST_REFRESH != yesterday

# ---------------------------------------------------------------------------
# Public APIs – read caches
# ---------------------------------------------------------------------------

def get_cached_yesterdays_analysis(*, force: bool = False) -> pd.DataFrame:
    global _YESTERDAYS_ANALYSIS, _LAST_REFRESH

    if force or _needs_refresh():
        tickers = get("tickers") or []
        try:
            _YESTERDAYS_ANALYSIS = get_yesterdays_ai_analysis(tickers)
            _LAST_REFRESH = date.today() - timedelta(days=1)
            logger.info(
                "YESTERDAYS_ANALYSIS cache refreshed (%d rows)",
                len(_YESTERDAYS_ANALYSIS),
            )
        except Exception as exc:
            logger.exception("Failed to refresh YESTERDAYS_ANALYSIS: %s", exc)
            _YESTERDAYS_ANALYSIS = pd.DataFrame()

    return _YESTERDAYS_ANALYSIS.copy() if _YESTERDAYS_ANALYSIS is not None else pd.DataFrame()




def get_cached_all_users_data(*, force: bool = False) -> pd.DataFrame:

    global _USERS_DATA

    if _USERS_DATA is None or force:
        try:
            df = get_all_users_data()
            # Normalize Telegram ID column to a canonical name used across the bot
            if not df.empty:
                lower_to_actual = {str(c).lower(): c for c in df.columns}
                # Prefer existing canonical name; otherwise, map common alternates
                if "telegram_user_id" not in lower_to_actual:
                    for alt in ("telegram_id", "tg_user_id", "tg_id", "tele_id"):
                        if alt in lower_to_actual:
                            df = df.rename(columns={lower_to_actual[alt]: "telegram_user_id"})
                            break
            _USERS_DATA = df
            logger.info("Users-data cache refreshed (%d rows)", len(_USERS_DATA))
        except Exception as exc:
            logger.exception("Failed to refresh users-data cache: %s", exc)
            return pd.DataFrame()
    return _USERS_DATA.copy() if _USERS_DATA is not None else pd.DataFrame()

# ---------------------------------------------------------------------------
# Public APIs – event buffering
# ---------------------------------------------------------------------------

def add_bot_event(event: Dict[str, Any]) -> None:
    """Add a single bot-action event to the in-memory buffer.

    If the buffer reaches `_EVENT_BATCH_SIZE` rows it is flushed to the
    database immediately.
    """
    global _EVENT_BUFFER
    _EVENT_BUFFER.append(event)
    logger.debug("Event appended to buffer; size=%d", len(_EVENT_BUFFER))

    if len(_EVENT_BUFFER) >= _EVENT_BATCH_SIZE:
        logger.info("Buffer reached %d events – triggering flush", _EVENT_BATCH_SIZE)
        flush_event_buffer()


def flush_event_buffer(force: bool = False) -> None:
    """Flush the in-memory event buffer to the DB if criteria met."""
    global _EVENT_BUFFER, _LAST_EVENT_FLUSH

    if not _EVENT_BUFFER:
        return

    # If force or time threshold reached
    time_since = (
        (datetime.utcnow() - _LAST_EVENT_FLUSH).total_seconds() if _LAST_EVENT_FLUSH else None
    )
    if force or len(_EVENT_BUFFER) >= _EVENT_BATCH_SIZE or (time_since and time_since >= _EVENT_FLUSH_SECONDS):
        events_to_flush = _EVENT_BUFFER[:]  # copy
        _EVENT_BUFFER.clear()
        inserted = insert_bot_actions(events_to_flush)
        if inserted:
            _LAST_EVENT_FLUSH = datetime.utcnow()
        logger.info("Flushed %d events to DB (buffer now %d)", inserted, len(_EVENT_BUFFER))

"""Utility helpers for reading/writing data to the MySQL database used by
`stock_bot`. Contains read helpers (AI analysis, users) and batched write
support for the `fact_telegram_bot_actions` table.
"""

from __future__ import annotations

import pandas as pd
import mysql.connector
import logging
from datetime import datetime, UTC
from typing import Iterable, Dict, Any, List

from database.connection import get_db_credentials

logger = logging.getLogger(__name__)

###############################################################################
# READ HELPERS (existing)
###############################################################################

# ---------------------------------------------------------------------------
# get_yesterdays_ai_analysis – reads yesterday's AI analysis for given tickers
# ---------------------------------------------------------------------------

def get_yesterdays_ai_analysis(tickers: list[str]) -> pd.DataFrame:
    """Return yesterday's AI-analysis rows for the supplied tickers.

    The query is parameterised – each ticker is bound individually to
    protect against SQL-injection.  Example produced SQL snippet::

        WHERE company_ticker IN (%s, %s, %s)
    """
    if not tickers:
        logger.info("get_yesterdays_ai_analysis called with empty ticker list – returning empty DataFrame")
        return pd.DataFrame()

    creds = get_db_credentials()
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()

        placeholders = ", ".join(["%s"] * len(tickers))
        query = f"""
            SELECT *
            FROM self_ai_analysis_ticker
            WHERE company_ticker IN ({placeholders})
              AND analysis_event_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
            ORDER BY analysis_event_date DESC
        """
        logger.info("Executing AI-analysis query for tickers: %s", tickers)
        cursor.execute(query, tuple(tickers))
        rows = cursor.fetchall()
        logger.info("Fetched %d AI-analysis rows from DB", len(rows))
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---------------------------------------------------------------------------
# get_all_users_data – reads full users data table
# ---------------------------------------------------------------------------

def get_all_users_data() -> pd.DataFrame:
    """Fetch all rows from ``fact_users_data_table`` and return a DataFrame."""
    creds = get_db_credentials()
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        query = "SELECT * FROM fact_users_data_table"
        logger.info("Executing users-data query")
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info("Fetched %d user-data rows from DB", len(rows))
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

###############################################################################
# WRITE HELPER – batch insert into fact_telegram_bot_actions
###############################################################################

actions_columns = [
    "user_id",
    "telegram_id",
    "event_time",
    "event_type",
    "user_email",
    "user_device",
    "user_plan",
    "kpi",
    "settings_action_trigger",
    "function_call_type",
    "before_change",
    "after_change",
    "product_purchase",
    "insertion_time",
]

# Template dict with all columns set to None – handy for building events
EVENT_TEMPLATE: Dict[str, Any] = {
    "user_id": None,            # VARCHAR(36)
    "telegram_id": None,        # VARCHAR(32)
    "event_time": None,         # TIMESTAMP
    "event_type": None,         # VARCHAR(50)
    "user_email": None,         # VARCHAR(255)
    "user_device": None,        # VARCHAR(100)
    "user_plan": None,          # VARCHAR(50)
    "kpi": None,                # VARCHAR(50)
    "settings_action_trigger": None,  # VARCHAR(60)
    "function_call_type": None,      # VARCHAR(60)
    "before_change": None,      # TEXT
    "after_change": None,       # TEXT
    "product_purchase": None,   # VARCHAR(50)
    "insertion_time": None,     # TIMESTAMP
}


def make_bot_event(user_id: str, event_type: str, **kwargs: Any) -> Dict[str, Any]:
    """Convenience helper to build an event dict matching the DB schema."""
    event = EVENT_TEMPLATE.copy()
    event["user_id"] = user_id
    event["event_type"] = event_type
    event.update(kwargs)

    return event

INSERT_SQL = (
    "INSERT IGNORE INTO fact_telegram_bot_actions ("
    + ", ".join(actions_columns)
    + ") VALUES ("
    + ", ".join(["%s"] * len(actions_columns))
    + ")"
)


def _tuple_from_event(event: Dict[str, Any]) -> tuple[Any, ...]:
    """Convert dictionary with event data to positional tuple for executemany."""
    # Fill missing keys with None; ensure timestamp fields default to now
    defaulted = {
        **{k: None for k in actions_columns},
        **event,
    }
    # Replace None with current UTC timestamp so NOT NULL columns are satisfied
    if defaulted["event_time"] is None:
        defaulted["event_time"] = datetime.now(UTC)
    if defaulted["insertion_time"] is None:
        defaulted["insertion_time"] = datetime.now(UTC)
    return tuple(defaulted[col] for col in actions_columns)


def insert_bot_actions(events: Iterable[Dict[str, Any]]) -> int:
    """Insert multiple bot-action events into the DB in one transaction.

    Parameters
    ----------
    events : iterable of dict
        Each dict must have at least ``user_id`` and ``event_type``. All
        other columns are optional.

    Returns
    -------
    int – number of rows successfully inserted.
    """
    events = list(events)
    if not events:
        logger.info("insert_bot_actions called with empty events list – nothing to do")
        return 0

    creds = get_db_credentials()
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        tuples: List[tuple[Any, ...]] = [_tuple_from_event(e) for e in events]
        logger.info("Inserting %d bot-action rows into DB", len(tuples))
        cursor.executemany(INSERT_SQL, tuples)
        conn.commit()
        logger.info("Committed %d bot-action rows", cursor.rowcount)
        return cursor.rowcount
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("Failed to insert bot-action events: %s", exc)
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

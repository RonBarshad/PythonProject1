"""
stock_bot/user_control.py
Mission: Centralised user-management processes (sign-up / sign-in / authentication / password reset)
that are callable from Telegram-bot handlers (but have no Telegram dependency themselves).

The module focuses on the single source-of-truth table `fact_users_data_table` and provides a
clear API for:
    • sign_up – create a new user row
    • sign_in – validate credentials & update last_login
    • authenticate – mark user as verified (via e-mail or Telegram)
    • forgot_password – allow the user to change their password
    • requires_relogin – helper to decide if the user must sign-in again (≥ N days)

All functions are synchronous (DB I/O is blocking) and return simple booleans / dicts so that
Telegram handlers can `await` them in an executor, or wrap them in their own async logic.

Security note: A strong password hashing algorithm (e.g. bcrypt/argon2) should be used in
production. Here we fall back to SHA-256 because it is available out-of-the-box and keeps the
project dependency-free.
"""

from __future__ import annotations

import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, UTC
import hashlib
import uuid
import logging
import secrets

from config.config import get  # DB credentials live in config

logger = logging.getLogger(__name__)

USER_TABLE = "fact_users_data_table"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db_credentials() -> Dict[str, str]:
    """Read DB credentials via project configuration."""
    return {
        "host": get("database.host"),
        "user": get("database.user"),
        "password": get("database.password"),
        "database": get("database.name"),
    }


def _hash_password(password: str) -> str:
    """Return a SHA-256 hex digest for *password*.  Replace with bcrypt in prod."""
    return hashlib.sha256(password.encode()).hexdigest()


def _execute_query(query: str, values: tuple | list | None = None, fetchone: bool = False, fetchall: bool = False):
    """Small helper to run a query and optionally fetch results.

    Commits on success. Rolls back & returns None on exceptions.
    """
    creds = _get_db_credentials()
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, values or ())
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        else:
            result = None
        conn.commit()
        return result
    except Error as exc:
        logger.error("Database error: %s", exc)
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sign_up(full_name: str, email: str, password: str, *, telegram_user_id: Optional[str] = None, phone_number: Optional[str] = None) -> bool:
    """Insert a new user; returns True on success, False if user already exists or error."""
    # Check duplicates (by e-mail or phone)
    duplicate_check = _execute_query(
        f"SELECT user_id FROM {USER_TABLE} WHERE email=%s OR phone_number=%s", (email, phone_number), fetchone=True
    )
    if duplicate_check:
        logger.info("sign_up: user already exists (email=%s, phone=%s)", email, phone_number)
        return False

    user_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    password_hash = _hash_password(password)

    insert_sql = f"""
        INSERT INTO {USER_TABLE} (
            user_id, creation_time, update_time, full_name, email, phone_number,
            password_hash, status, telegram_user_id, last_login, plan_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s, %s, 'free')
    """
    ok = _execute_query(
        insert_sql,
        (
            user_id,
            now,
            now,
            full_name,
            email,
            phone_number,
            password_hash,
            telegram_user_id,
            now,
        ),
    )
    if ok is None:  # _execute_query returns None for non-select queries on success
        logger.info("sign_up: new user created user_id=%s", user_id)
        return True
    return False


def sign_in(email: str, password: str) -> bool:
    """Validate user/password. On success update `last_login` and return True."""
    user_row = _execute_query(
        f"SELECT user_id, password_hash FROM {USER_TABLE} WHERE email=%s", (email,), fetchone=True
    )
    if not user_row:
        logger.info("sign_in: e-mail not found (%s)", email)
        return False

    if user_row["password_hash"] != _hash_password(password):
        logger.info("sign_in: wrong password for %s", email)
        return False

    # Update last_login
    _execute_query(
        f"UPDATE {USER_TABLE} SET last_login=%s WHERE user_id=%s",
        (datetime.now(UTC), user_row["user_id"]),
    )
    return True


def authenticate_via_telegram(telegram_user_id: str) -> bool:
    """Mark the user as authenticated using their Telegram id."""
    updated = _execute_query(
        f"UPDATE {USER_TABLE} SET status='active' WHERE telegram_user_id=%s", (telegram_user_id,)
    )
    return updated is None


def authenticate_via_email(email: str) -> bool:
    """Mark the user as authenticated using their e-mail address."""
    updated = _execute_query(
        f"UPDATE {USER_TABLE} SET status='active' WHERE email=%s", (email,)
    )
    return updated is None


def forgot_password(email: str, new_password: str) -> bool:
    """Reset the user's password and update change counters/timestamps."""
    new_hash = _hash_password(new_password)
    now = datetime.now(UTC)
    sql = f"""
        UPDATE {USER_TABLE}
        SET password_hash=%s,
            user_password_change_amount = COALESCE(user_password_change_amount, 0) + 1,
            last_user_password_change_time=%s,
            update_time=%s,
            update_amount=update_amount+1
        WHERE email=%s
    """
    updated = _execute_query(sql, (new_hash, now, now, email))
    return updated is None


def requires_relogin(last_login: datetime | None, *, days: int = 10) -> bool:
    """Return True if *last_login* is older than *days* days (UTC-aware)."""
    if not last_login:
        return True
    if last_login.tzinfo is None:
        last_login = last_login.replace(tzinfo=UTC)
    return datetime.now(UTC) - last_login >= timedelta(days=days)


def is_user_registered(telegram_user_id: str | int, *, force_refresh: bool = False) -> bool:
    """Return True if a user with this Telegram-ID exists in the cache and is active.

    Args:
        telegram_user_id: numeric or string Telegram user id.
        force_refresh: pass True to reload the users-data cache from DB.
    """
    from . import cache as _cache  # local import to avoid circular dependencies
    import pandas as pd

    df: pd.DataFrame = _cache.get_cached_all_users_data(force=force_refresh)
    mask = df["telegram_user_id"].astype(str).str.strip() == str(telegram_user_id).strip()
    if not mask.any():
        return False
    if "status" in df.columns:
        return df.loc[mask, "status"].iloc[0] == "active"
    return True

# ---------------------------------------------------------------------------
# Convenience fetchers (can be useful for bot logic)
# ---------------------------------------------------------------------------

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _execute_query(
        f"SELECT * FROM {USER_TABLE} WHERE email=%s", (email,), fetchone=True
    )


def get_user_by_telegram_id(telegram_user_id: str) -> Optional[Dict[str, Any]]:
    return _execute_query(
        f"SELECT * FROM {USER_TABLE} WHERE telegram_user_id=%s", (telegram_user_id,), fetchone=True
    )

# ---------------------------------------------------------------------------
#  Inventory helpers
# ---------------------------------------------------------------------------

def get_allowed_tickers(plan_type: str | None) -> int:
    """Return how many tickers the plan allows."""
    if plan_type == "pro":
        return 20
    if plan_type == "premium":
        return 50
    # default free
    return 5


def update_user_tickers(user_id: str, tickers: list[str]) -> bool:
    """Persist comma-separated ticker list for a user."""
    tickers_str = ",".join([t.upper() for t in tickers])
    res = _execute_query(
        f"UPDATE {USER_TABLE} SET tickers=%s, update_time=%s, update_amount=update_amount+1 WHERE user_id=%s",
        (tickers_str, datetime.utcnow(), user_id),
    )
    return res is None









async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user signup command."""
    if not update.message or not update.message.text:
        await update.message.reply_text("Please provide signup details")
        return

    try:
        _, full_name, email, password = update.message.text.split(maxsplit=3)
    except ValueError:
        await update.message.reply_text("Usage: /signup <full-name> <email> <password>")
        return

    if not update.effective_user:
        await update.message.reply_text("Could not determine Telegram user")
        return

    ok = sign_up(full_name, email, password,
                 telegram_user_id=str(update.effective_user.id))
    if ok:
        await update.message.reply_text("✅ Sign-up successful! You can /login now.")
    else:
        await update.message.reply_text("❌ That email is already registered.")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user login command."""
    if not update.message or not update.message.text:
        await update.message.reply_text("Please provide login details")
        return

    try:
        _, email, password = update.message.text.split(maxsplit=2)
    except ValueError:
        await update.message.reply_text("Usage: /login <email> <password>")
        return

    ok = sign_in(email, password)
    if ok:
        await update.message.reply_text("✅ Logged in!")
        await send_menu(update, context)
    else:
        await update.message.reply_text("❌ Wrong email or password.")


async def forgot_pw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password reset command."""
    if not update.message or not update.message.text:
        await update.message.reply_text("Please provide email and new password")
        return

    try:
        _, email, new_pw = update.message.text.split(maxsplit=2)
    except ValueError:
        await update.message.reply_text("Usage: /forgot <email> <new-password>")
        return

    ok = forgot_password(email, new_pw)
    if ok:
        await update.message.reply_text("✅ Password updated. Use /login to sign in.")
    else:
        await update.message.reply_text("❌ Could not reset password. Please verify your email is correct.")




# ---------------------------------------------------------------------------
#  Email verification
# ---------------------------------------------------------------------------

def _generate_token() -> str:
    return secrets.token_urlsafe(32)

def create_email_verification(user_id: str, email: str) -> str:
    token = _generate_token()
    _execute_query(
        f"UPDATE {USER_TABLE} SET email_verify_token=%s, email_verified=0 "
        f"WHERE user_id=%s", (token, user_id))
    return token

def verify_email_token(email: str, token: str) -> bool:
    row = _execute_query(
        f"SELECT user_id FROM {USER_TABLE} WHERE email=%s AND email_verify_token=%s",
        (email, token), fetchone=True)
    if not row:
        return False
    _execute_query(
        f"UPDATE {USER_TABLE} SET email_verified=1, email_verify_token=NULL WHERE user_id=%s",
        (row['user_id'],))
    return True

    

    
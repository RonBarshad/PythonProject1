"""
stock_bot/stock_analysis.py
Mission: Inline, protected Stock Analysis flow.

When a user taps "📈 Stock Analysis":
  1) Show last update time for daily analysis
  2) Render inline buttons for the user's tickers (in-conversation, not reply keyboard)
  3) Include a back-to-menu button

When a ticker is pressed:
  - Fetch analysis text from cache.get_cached_yesterdays_analysis() for that ticker
  - Send it as a protected message (not copyable/forwardable)
"""

from __future__ import annotations

import sys, pathlib
# Ensure project root on sys.path when run as a module or script
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from typing import List, Optional
import re
from datetime import date, timedelta
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from stock_bot import cache
from stock_bot.user_messages_config import get_menu_message_and_keyboard

logger = logging.getLogger(__name__)


def _parse_user_tickers(raw_value: Optional[str]) -> List[str]:
    if not raw_value:
        return []
    return [t.strip().upper() for t in str(raw_value).split(",") if t and t.strip()]


def _build_inline_keyboard_from_tickers(tickers: List[str], per_row: int = 3) -> InlineKeyboardMarkup:
    rows = []
    row: List[InlineKeyboardButton] = []
    for idx, t in enumerate(tickers):
        row.append(InlineKeyboardButton(text=t, callback_data=f"sa_ticker:{t}"))
        if (idx + 1) % per_row == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # Back to menu row
    rows.append([InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="sa_back")])
    return InlineKeyboardMarkup(rows)


async def show_stock_analysis_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    internal_user_id: str,
    user_id: int | str,
    user_email: Optional[str],
    user_plan: Optional[str],
):
    """Render last-update info and inline ticker buttons for this user."""
    user_df = cache.get_cached_all_users_data()
    mask = user_df["user_id"].astype(str).str.strip() == str(internal_user_id).strip()
    if not mask.any():
        await update.message.reply_text("No user record found. Please /start again.")
        return

    row = user_df.loc[mask].iloc[0]
    tickers = _parse_user_tickers(row.get("tickers"))

    df = cache.get_cached_yesterdays_analysis()
    last_update_text = "unknown"
    try:
        if not df.empty:
            # Prefer analysis_event_date; fall back to insertion_time
            if "analysis_event_date" in df.columns and df["analysis_event_date"].notna().any():
                last_update_text = str(df["analysis_event_date"].max())
            elif "insertion_time" in df.columns and df["insertion_time"].notna().any():
                last_update_text = str(df["insertion_time"].max())
            else:
                last_update_text = str(date.today() - timedelta(days=1))
    except Exception as exc:
        logger.warning("Failed computing last update time: %s", exc)

    if not tickers:
        await update.message.reply_text(
            f"Last daily analysis update: {last_update_text}\n"
            "You have no tickers configured yet. Go to ⚙️ Settings → 📋 Stocks Inventory."
        )
        return

    keyboard = _build_inline_keyboard_from_tickers(tickers)
    await update.message.reply_text(
        f"Last daily analysis update: {last_update_text}\nSelect a ticker:",
        reply_markup=keyboard,
    )


async def _send_protected_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: str):
    """Lookup yesterday's analysis for ticker and send as a protected message."""
    df = cache.get_cached_yesterdays_analysis()
    if df.empty:
        await update.callback_query.message.reply_text(
            f"No analysis available for {ticker}.",
        )
        return

    df_t = df.loc[(df["company_ticker"].astype(str).str.upper() == ticker.upper())]
    try:
        logger.info("stock_analysis: query result rows=%d for ticker=%s", len(df_t), ticker,
                    extra={"handler": "stock_analysis", "ticker": ticker})
    except Exception:
        pass
    if df_t.empty:
        await update.callback_query.message.reply_text(
            f"No analysis found for {ticker}.",
        )
        return

    # Choose the most recent row if insertion_time present
    if "insertion_time" in df_t.columns and df_t["insertion_time"].notna().any():
        df_t = df_t.sort_values("insertion_time", ascending=False)
    raw_text = str(df_t.iloc[0].get("text_analysis") or "No analysis text available.")
    try:
        logger.info("Formatting tagged analysis (raw_len=%d)", len(raw_text),
                    extra={"handler": "stock_analysis", "ticker": ticker})
        # Include a short preview for observability; keep it small to avoid log bloat
        preview = raw_text[:500].replace("\n", " ")
        logger.info("raw_text_preview=%s", preview, extra={"handler": "stock_analysis", "ticker": ticker})
    except Exception:
        pass
    pretty_text = _format_tagged_analysis_for_text(raw_text, ticker=ticker)
    try:
        preview_pretty = pretty_text[:500].replace("\n", " ")
        logger.info("pretty_text_preview=%s", preview_pretty, extra={"handler": "stock_analysis", "ticker": ticker})
    except Exception:
        pass

    # Protect content from forwarding/saving
    await update.callback_query.message.reply_text(
        pretty_text,
        protect_content=True,
        disable_web_page_preview=True,
    )
    try:
        logger.info("Sent formatted analysis (len=%d)", len(pretty_text),
                    extra={"handler": "stock_analysis", "ticker": ticker})
    except Exception:
        pass


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard presses for the stock analysis flow."""
    query = update.callback_query
    data = query.data or ""
    await query.answer()

    if data == "sa_back":
        # Show main menu (reply keyboard)
        menu_message, keyboard = get_menu_message_and_keyboard()
        await query.message.reply_text(menu_message, reply_markup=keyboard)
        return

    if data.startswith("sa_ticker:"):
        ticker = data.split(":", 1)[1]
        await _send_protected_analysis(update, context, ticker)
        return

    # Unknown callback
    await query.message.reply_text("Unknown action.")



def _format_tagged_analysis_for_text(raw: Optional[str], *, ticker: Optional[str] = None) -> str:
    """
    Convert a single-line tagged analysis paragraph into a readable, emoji-titled
    multi-section plain text for Telegram.
    Expected tags: <TA> <CN> <WN> <IC> <COMP> <LEGAL> <FIN>
    """
    if not raw:
        return "No analysis content available."

    sections = [
        ("TA", "Technical Analysis 📈"),
        ("CN", "Company News 📰"),
        ("WN", "World News 🌍"),
        ("IC", "Industry Changes 🏭"),
        ("COMP", "Competitors 🆚"),
        ("LEGAL", "Legal ⚖️"),
        ("FIN", "Financial 💰"),
    ]

    def is_no_data(text: str) -> bool:
        if not text:
            return True
        normalized = text.strip().lower()
        normalized = re.sub(r'[«»“”"\']', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized in {"no significant data", "no significant data.", "n/a", "none", "-"}

    formatted_parts: List[str] = []
    for code, title in sections:
        pattern = rf"<{code}>(.*?)(?:</{code}>|(?=\s*<[A-Z]+>|$))"
        match = re.search(pattern, raw, re.DOTALL)
        if not match:
            alt_pattern = rf"<{code}>(.*?)(?=\s*<[A-Z]+>|$)"
            match = re.search(alt_pattern, raw, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if not is_no_data(content):
                content_clean = re.sub(r"\s+", " ", content).strip()
                formatted_parts.append(f"{title}\n{content_clean}")
    # Logging branch counts to help diagnose formatting issues
    try:
        import logging as _logging
        _log = _logging.getLogger(__name__)
        _log.info("_format_tagged_analysis_for_text: sections_kept=%d", len(formatted_parts),
                 extra={"handler": "stock_analysis", "ticker": ticker})
    except Exception:
        pass
    return "\n\n".join(formatted_parts) if formatted_parts else raw


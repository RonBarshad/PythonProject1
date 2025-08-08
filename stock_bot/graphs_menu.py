from __future__ import annotations

from typing import List
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from stock_bot import cache
from stock_bot.db_data_handaling import make_bot_event
from datetime import datetime, UTC
from graphs.candlestick_chart import generate_candlestick_with_kpis

logger = logging.getLogger(__name__)

AVAILABLE_KPIS = [
    "sma20", "sma50", "sma200", "ema20", "rsi14", "macd", "macd_signal", "macd_hist",
    "swing_high_20", "swing_low_20"
]


def _parse_user_tickers(row_value) -> List[str]:
    if not row_value:
        return []
    return [t.strip().upper() for t in str(row_value).split(",") if t and t.strip()]


def _example_for_ticker(ticker: str, idx: int) -> str:
    # Rotate examples for variety
    patterns = [
        f"/{ticker} rsi14 45 days",
        f"/{ticker} sma20, sma50, sma200 60 days",
        f"/{ticker} macd_signal, macd_hist 30 days",
    ]
    return patterns[idx % len(patterns)]


async def show_graphs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           *, internal_user_id: str, user_id: str | int,
                           user_email: str | None, user_plan: str | None) -> None:
    # Build example buttons per user ticker
    df_users = cache.get_cached_all_users_data()
    row = df_users.loc[df_users["user_id"] == internal_user_id]
    tickers = _parse_user_tickers(row["tickers"].iloc[0] if not row.empty else "")

    rows: List[List[InlineKeyboardButton]] = []
    for idx, t in enumerate(tickers):
        example = _example_for_ticker(t, idx)
        rows.append([InlineKeyboardButton(text=example, callback_data=f"gm_example:{example}")])
    rows.append([InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="gm_back")])
    keyboard = InlineKeyboardMarkup(rows)

    await update.message.reply_text(
        "Graph menu: choose an example or type your own in the format\n"
        "/AAPL sma20 60 days\n"
        "/AAPL sma20, sma50 60 days\n\n"
        "Available KPIs: " + ", ".join(AVAILABLE_KPIS),
        reply_markup=keyboard,
    )

    # Record event
    event = make_bot_event(
        internal_user_id,
        "graphs_menu_opened",
        telegram_id=str(user_id),
        user_email=user_email,
        user_plan=user_plan,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)


async def handle_graphs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    await query.answer()
    if data == "gm_back":
        # import lazily to avoid cycle
        from stock_bot.user_messages_config import get_menu_message_and_keyboard
        message, kb = get_menu_message_and_keyboard()
        await query.message.reply_text(message, reply_markup=kb)
        return

    if data.startswith("gm_example:"):
        example = data.split(":", 1)[1]
        # Expected: /AAPL sma20, sma50 60 days
        try:
            parts = example.strip("/").split()
            ticker = parts[0]
            # KPIs may be comma-separated list
            kpis_raw = parts[1:-2]  # handles single or multiple entries separated by commas
            kpi_str = " ".join(kpis_raw).replace(",", " ")
            kpis = [k for k in kpi_str.split() if k]
            days = int(parts[-2]) if parts[-1].lower().startswith("days") else int(parts[-1])
        except Exception:
            await query.message.reply_text("Invalid example format.")
            return

        image = generate_candlestick_with_kpis(ticker, days, kpis)
        if image:
            await query.message.reply_photo(photo=image, protect_content=True)
        else:
            await query.message.reply_text("Failed to generate graph.")

        # Log event
        await _record_graph_event_from_example(update, ticker, kpis, days)


async def _record_graph_event_from_example(update: Update, ticker: str, kpis: List[str], days: int) -> None:
    try:
        # We don't have internal_user_id here; keep minimal fields
        event = {
            "user_id": None,
            "telegram_id": str(update.effective_user.id) if update.effective_user else None,
            "event_time": datetime.now(UTC),
            "event_type": "graph_asked",
            "kpi": ",".join(kpis),
            "function_call_type": "example",
            "before_change": None,
            "after_change": f"{ticker} {kpis} {days}d",
            "insertion_time": datetime.now(UTC),
        }
        cache.add_bot_event(event)
    except Exception:
        pass



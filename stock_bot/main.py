"""
main.py
Main entry point for the new bot.
This script initializes and runs a Telegram bot using credentials from the config.
"""

import sys, pathlib
# Ensure project root is on sys.path so that 'config' package can be resolved
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from config.config import get  # Import the config getter to access API keys and settings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
from telegram.error import TelegramError
import logging
import asyncio
import re
from datetime import time as dtime, datetime, UTC
from stock_bot.user_messages_config import get_welcome_message, get_menu_message_and_keyboard, get_login_message_and_keyboard, get_settings_message_and_keyboard
from stock_bot import stock_analysis
from stock_bot import graphs_menu
from stock_bot import cache, user_control # provides daily-refreshed YESTERDAYS_ANALYSIS
from stock_bot.db_data_handaling import make_bot_event
from notifications.email_sender import send_email
from stock_bot.user_control import create_email_verification, verify_email_token
# Correlation context
import uuid

# Configure logging
from utils.logging_setup import setup_logging
from utils.log_context import ContextFilter, request_id_ctx, user_id_ctx, telegram_id_ctx, username_ctx, app_user_id_ctx
from utils.logging_utils import log_call
from utils.metrics import start_metrics_server, handler_calls, handler_duration

setup_logging(logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Logging configured", extra={"handler": "init"})
# Attach context filter at root so all module logs get context fields
logging.getLogger().addFilter(ContextFilter())


# ---------------------------------------------------------------------------
#  Text-routing helpers (button labels → handler coroutine)
# ---------------------------------------------------------------------------

# Map exact button/text labels to a coroutine that handles them (pre-auth)


async def try_route_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """If text matches a pre-auth route, call its handler and return True."""
    text = (update.message.text or "") if update.message else ""
    handler = _TEXT_ROUTES.get(text)
    if handler:
        await handler(update, context)
        return True
    return False


def register_text_routes(app):
    """Register regex MessageHandlers for each static text route."""
    for label, func in _TEXT_ROUTES.items():
        pattern = f"^{re.escape(label)}$"
        app.add_handler(MessageHandler(filters.Regex(pattern), func))


# ---------------------------------------------------------------------------
#  Helpers – detect telegram id column & build masks safely
# ---------------------------------------------------------------------------

def _find_telegram_id_column(df) -> str | None:
    if df is None or df.empty:
        return None
    # Try common names (case-insensitive)
    candidates = [
        "telegram_user_id", "telegram_id", "tg_user_id", "tg_id", "tele_id"
    ]
    lower_to_actual = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_to_actual:
            return lower_to_actual[cand]
    # Fallback: any column that includes both 'telegram' and 'id'
    for col in df.columns:
        lc = str(col).lower()
        if "telegram" in lc and "id" in lc:
            return col
    return None

def _mask_by_telegram_id(df, tg_id: str):
    col = _find_telegram_id_column(df)
    if not col:
        return None, None
    try:
        mask = df[col].astype(str).str.strip() == str(tg_id).strip()
        return mask, col
    except Exception:
        return None, col
async def _get_user_context(update: Update):
    """Return (internal_user_id, user_id, user_email, user_plan) from cache.

    Falls back to ("unknown", tg_id, None, None) if not found.
    """
    try:
        tg_id = update.effective_user.id if update.effective_user else None
        if tg_id is None:
            return "unknown", "unknown", None, None
        df_users = cache.get_cached_all_users_data()
        if df_users is None or df_users.empty:
            return "unknown", tg_id, None, None
        mask = df_users["telegram_user_id"].astype(str).str.strip() == str(tg_id).strip() if "telegram_user_id" in df_users.columns else None
        if mask is None or not mask.any():
            mask, _ = _mask_by_telegram_id(df_users, tg_id)
        if mask is None or not mask.any():
            return "unknown", tg_id, None, None
        row = df_users.loc[mask].iloc[0]
        return row.get("user_id") or "unknown", tg_id, row.get("email"), row.get("plan_type")
    except Exception:
        return "unknown", "unknown", None, None



# ---------------------------------------------------------------------------
#  App routes
# ---------------------------------------------------------------------------

async def _handle_stock_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 internal_user_id: str, user_id: int | str,
                                 user_email: str | None, user_plan: str | None):
    # Log event then show the inline analysis menu
    event = make_bot_event(
        internal_user_id,
        "stock_analysis_pushed",
        telegram_id=str(user_id),
        user_email=user_email,
        user_plan=user_plan,
        user_device=update.effective_user.language_code if update.effective_user else None,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)
    await stock_analysis.show_stock_analysis_menu(
        update, context,
        internal_user_id=internal_user_id,
        user_id=user_id,
        user_email=user_email,
        user_plan=user_plan,
    )

async def _handle_graphs(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         internal_user_id: str, user_id: int | str,
                         user_email: str | None, user_plan: str | None):
    await graphs_menu.show_graphs_menu(
        update, context,
        internal_user_id=internal_user_id,
        user_id=user_id,
        user_email=user_email,
        user_plan=user_plan,
    )

async def _handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           internal_user_id: str, user_id: int | str,
                           user_email: str | None, user_plan: str | None):
    await update.effective_message.reply_text("Opening settings …")
    event = make_bot_event(
        internal_user_id,
        "settings_opened",
        telegram_id=str(user_id),
        user_email=user_email,
        user_plan=user_plan,
        user_device=update.effective_user.language_code if update.effective_user else None,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)
    await send_settings_menu(update, context)




async def _handle_login_signup(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               internal_user_id: str, user_id: int | str,
                               user_email: str | None, user_plan: str | None):
    await send_login_menu(update, context)

async def _handle_payments(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           internal_user_id: str, user_id: int | str,
                           user_email: str | None, user_plan: str | None):
    await update.effective_message.reply_text("Payments management feature coming soon.")

async def _handle_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               internal_user_id: str, user_id: int | str,
                               user_email: str | None, user_plan: str | None):
    await update.effective_message.reply_text(f"Your email: {user_email or 'unknown'}\nPlan: {user_plan or 'unknown'}")

async def _handle_stocks_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   internal_user_id: str, user_id: int | str,
                                   user_email: str | None, user_plan: str | None):
    """Start inventory edit flow."""
    df_users = cache.get_cached_all_users_data()
    row = df_users.loc[df_users["user_id"] == internal_user_id].iloc[0]
    current = (row.get("tickers") or "").strip()
    allowed = user_control.get_allowed_tickers(user_plan)
    if current:
        await update.effective_message.reply_text(
            f"Your current inventory ({len(current.split(','))}/{allowed}): {current}")
    else:
        await update.effective_message.reply_text(
            f"You have no stocks yet. Example: AAPL, MSFT\nMaximum allowed: {allowed}")
    event = make_bot_event(
        internal_user_id,
        "stocks_inventory_opened",
        telegram_id=str(user_id),
        user_email=user_email,
        user_plan=user_plan,
        user_device=update.effective_user.language_code if update.effective_user else None,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)
    await update.effective_message.reply_text("Send a comma-separated list of tickers to set your inventory:")
    context.user_data["awaiting_inventory"] = {"user_id": internal_user_id, "allowed": allowed}


async def _handle_stock_weights(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                internal_user_id: str, user_id: int | str,
                                user_email: str | None, user_plan: str | None):
    await update.effective_message.reply_text("Stock weights feature coming soon.")




# ---------------------------------------------------------------------------
#  Login conversation
# ---------------------------------------------------------------------------
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)
SIGNUP_NAME, SIGNUP_EMAIL, SIGNUP_PASSWORD = range(3)
FORGOT_EMAIL, FORGOT_PASSWORD = range(2)
INVENTORY_INPUT = range(1)


async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auth_flow_active"] = True
    await update.message.reply_text("Please enter your e-mail address:")
    return LOGIN_EMAIL

async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['login_email'] = update.message.text.strip()
    # ask for password
    await update.message.reply_text("Now enter your password (it will be deleted for privacy):")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate credentials; log event; finish conversation."""
    pwd_msg = update.message
    pwd = pwd_msg.text.strip()
    # remove the password message for privacy
    try:
        await pwd_msg.delete()
    except Exception:
        pass

    email = context.user_data.get("login_email")
    if not user_control.sign_in(email, pwd):
        await update.message.reply_text("❌ Wrong credentials.")
        logger.error("Wrong credentials for email=%s", email)
        # Clear auth flow flags
        context.user_data.pop("auth_flow_active", None)
        context.user_data.pop("login_email", None)
        return ConversationHandler.END

    # success – refresh users cache and fetch fresh row
    df_users = cache.get_cached_all_users_data(force=True)
    mask = df_users["email"].astype(str).str.strip() == str(email).strip()
    if not mask.any():
        logger.error("User row missing after successful sign_in for email=%s", email)
        return ConversationHandler.END

    row = df_users.loc[mask].iloc[0]
    internal_user_id = row["user_id"]
    telegram_id = row["telegram_user_id"]
    user_plan = row.get("plan_type")

    await update.message.reply_text("✅ Logged in!")

    event = make_bot_event(
        internal_user_id,
        "login_success",
        telegram_id=str(telegram_id),
        user_email=email,
        user_plan=user_plan,
        user_device=update.effective_user.language_code if update.effective_user else None,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)
    logger.info("Login success %s", email)
    # Clear auth flow flags
    context.user_data.pop("auth_flow_active", None)
    context.user_data.pop("login_email", None)
    return ConversationHandler.END

# ---------------------------------------------------------------------------
#  Sign-up conversation
# ---------------------------------------------------------------------------
async def signup_start(update, context):
    context.user_data["signup_in_progress"] = True       # flag to indicate signup is in progress
    context.user_data["auth_flow_active"] = True
    await update.message.reply_text("Enter your full name:")
    return SIGNUP_NAME

async def signup_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['signup_name'] = update.message.text.strip()
    await update.message.reply_text("Enter your e-mail address:")
    return SIGNUP_EMAIL

async def signup_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['signup_email'] = update.message.text.strip()
    await update.message.reply_text("Choose a password (it will be deleted for privacy):")
    return SIGNUP_PASSWORD

async def signup_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd_msg = update.message
    pwd = pwd_msg.text.strip()
    try:
        await pwd_msg.delete()
    except Exception:
        pass

    full_name = context.user_data.get('signup_name')
    email = context.user_data.get('signup_email')
    tg_id = str(update.effective_user.id) if update.effective_user else None
    ok = user_control.sign_up(full_name, email, pwd, telegram_user_id=tg_id)
    if not ok:
        await update.message.reply_text("❌ Sign-up failed (e-mail or phone may already exist).")
        logger.error("Sign-up failed for email=%s", email)
        context.user_data.pop("signup_in_progress", None)
        context.user_data.pop("auth_flow_active", None)
        return ConversationHandler.END

    # --- success path ---

    # success – refresh users cache and fetch fresh row
    df_users = cache.get_cached_all_users_data(force=True)
    row_mask = df_users["email"].astype(str).str.strip() == email.strip()
    if not row_mask.any():
        logger.error("User row missing after successful sign_up for email=%s", email)
        context.user_data.pop("signup_in_progress", None)
        return ConversationHandler.END

    row = df_users.loc[row_mask].iloc[0]
    internal_user_id = row["user_id"]
    telegram_id      = row["telegram_user_id"]
    user_plan        = row.get("plan_type")

    # send verification email now that we have user_id
    token = create_email_verification(internal_user_id, email)
    verify_link = f"https://your-domain.com/verify?email={email}&token={token}"
    send_email(
        email,
        subject="Verify your email for Stock Bot",
        body=(
            "Click to verify: " + verify_link + "\n\n" +
            "Or copy this code and send it to the bot: " + token
        )
    )
    await update.message.reply_text("✅ Sign-up successful! Check your email for a verification link or code.")
    context.user_data["awaiting_email_token"] = email

    event = make_bot_event(
        internal_user_id,
        "signup_success",
        telegram_id=str(telegram_id),
        user_email=email,
        user_plan=user_plan,
        user_device=update.effective_user.language_code if update.effective_user else None,
        insertion_time=datetime.now(UTC),
    )
    cache.add_bot_event(event)

    # clear flag and finish
    context.user_data.pop("signup_in_progress", None)
    context.user_data.pop("auth_flow_active", None)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
#  Forgot-password conversation
# ---------------------------------------------------------------------------
async def forgot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auth_flow_active"] = True
    await update.message.reply_text("Enter your registered e-mail address:")
    return FORGOT_EMAIL

async def forgot_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['forgot_email'] = update.message.text.strip()
    await update.message.reply_text("Enter a NEW password (it will be deleted for privacy):")
    return FORGOT_PASSWORD

async def forgot_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    new_pwd = msg.text.strip()
    try:
        await msg.delete()
    except Exception:
        pass

    email = context.user_data.get('forgot_email')
    ok = user_control.forgot_password(email, new_pwd)
    if ok:
        await update.message.reply_text("✅ Password updated. You can now log in with /login")
        cache.get_cached_all_users_data(force=True)
        logger.info("Password reset for %s", email)
    else:
        await update.message.reply_text("❌ Could not reset password (email not found).")
        logger.error("Password reset failed for %s", email)
    # Clear flags
    context.user_data.pop('forgot_email', None)
    context.user_data.pop('auth_flow_active', None)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
#  App routes
# ---------------------------------------------------------------------------


_APP_ROUTES = {
    "📈 Stock Analysis": _handle_stock_analysis,
    "📊 Graphs": _handle_graphs,
    "⚙️ Settings": _handle_settings,
    "🔄 Login/Signup": _handle_login_signup,
    "💰 Payments": _handle_payments,
    "👤 User Details": _handle_user_details,
    "📋 Stocks Inventory": _handle_stocks_inventory,
    "⚖️ Stock Weights": _handle_stock_weights,
}

_TEXT_ROUTES = {}

# ---------------------------------------------------------------------------
#  Insert data to db
# ---------------------------------------------------------------------------

insert_data_to_db = {
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




@log_call("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command.

    1. Validate that the Telegram user exists in our users table.
    2. If not registered – ask them to register.
    3. If registered – send a short welcome text and the main menu
       (with reply-keyboard) so they can continue.
    """

    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    if update.effective_user:
        user_id_ctx.set(str(update.effective_user.id))
        telegram_id_ctx.set(str(update.effective_user.id))
    user_id = str(update.effective_user.id) if update.effective_user else None
    logger.info("Received /start command from user_id=%s", user_id)

    df_users = cache.get_cached_all_users_data()
    registered_mask = df_users["telegram_user_id"].astype(str).str.strip() == (user_id or "")

    # If not found, refresh once (new user may have just signed-up in parallel)
    if not registered_mask.any():
        df_users = cache.get_cached_all_users_data(force=True)
        registered_mask = df_users["telegram_user_id"].astype(str).str.strip() == (user_id or "")

    if not registered_mask.any():
        # Show login / signup keyboard instead of plain text
        await send_login_menu(update, context)
        return

    # Optionally require verified email
    row = df_users.loc[registered_mask].iloc[0]
    if not row.get("email_verified"):
        await update.message.reply_text("📧 Please verify your e-mail first – check your inbox and paste the code here.")
        context.user_data["awaiting_email_token"] = row["email"]
        return

    # 1) Send greeting
    await update.message.reply_text(get_welcome_message())
    # 2) Present the main menu
    await send_menu(update, context)




async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo any received message."""
    logger.info(f"Echoing message from user {update.effective_user.id}: {update.message.text}")
    message, keyboard = get_menu_message_and_keyboard()
    await update.message.reply_text(message, reply_markup=keyboard)




async def check_bot_connection(bot_token: str) -> bool:
    """Check if the bot can connect to Telegram using the provided token."""
    from telegram import Bot
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as @{me.username} (id: {me.id})")
        return True
    except TelegramError as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during bot connection: {e}")
        return False



# Take care of the user inputs that are not commands or menu buttons
async def refresh_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to refresh the users-data cache on demand."""
    df = cache.get_cached_all_users_data(force=True)
    await update.message.reply_text(f"Users data refreshed ({len(df)} rows).")




# ---------------------------------------------------------------------------
#  Send menu / login menu functions
# ---------------------------------------------------------------------------

async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu along with its reply keyboard.

    Used by /start and by the fallback handler to keep the menu easily
    accessible for the user.
    """
    menu_message, keyboard = get_menu_message_and_keyboard()
    await update.effective_message.reply_text(menu_message, reply_markup=keyboard)


async def send_login_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the login menu along with its reply keyboard.

    Avoid sending if an auth flow is already active for this user to
    prevent duplicate menus spamming during conversations.
    """
    if context.user_data.get("auth_flow_active"):
        return
    login_message, keyboard = get_login_message_and_keyboard()
    await update.effective_message.reply_text(login_message, reply_markup=keyboard)


async def send_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the settings menu along with its reply keyboard."""
    settings_message, keyboard = get_settings_message_and_keyboard()
    await update.effective_message.reply_text(settings_message, reply_markup=keyboard)





async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the main menu when the user's message is not recognised.

    If the text is neither a command nor one of the predefined menu
    button labels, we assume the user is lost and proactively present
    the menu so they can continue interacting.
    """
    user_input = (update.message.text or "") if update.message else ""
    # Flatten MENU_BUTTONS and include pre/post-auth button labels
    from stock_bot.user_messages_config import MENU_BUTTONS
    button_labels = {label for row in MENU_BUTTONS for label in row}
    button_labels.update(_TEXT_ROUTES.keys())
    button_labels.update(_APP_ROUTES.keys())
    # Don't send menu if input is one of our buttons, a command,
    # or if an auth/settings flow is active
    if (
        user_input in button_labels
        or user_input.strip().startswith("/")
        or context.user_data.get("auth_flow_active")
        or context.user_data.get("signup_in_progress")
        or context.user_data.get("awaiting_email_token")
        or context.user_data.get("awaiting_inventory")
    ):
        return
    await send_menu(update, context)







async def login_or_signup_or_forgot_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the login, signup, or forgot password commands."""
    await update.message.reply_text("Please log in or register if you are a new user.")
    
    keyboard = [
        ["Login", "Sign Up"],
        ["Forgot my password"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Please choose an option:",
        reply_markup=reply_markup
    )



# Create a local variable to hold yesterday's AI analysis data as a DataFrame for use by the Telegram bot.

# Example: Preload yesterday's analysis for all tickers in config at startup (can be used/cached by handlers)
# Warm up the cache so the first user gets fast data.
try:
    cache.get_cached_yesterdays_analysis(force=True)
except Exception as e:
    logger.warning("Initial analysis cache failed: %s", e)



@log_call("monitored_echo")
async def monitored_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain-text messages that are NOT bot commands.

    Logs the incoming text, determines whether it corresponds to one of
    the main-menu buttons, and sends a placeholder response for each
    recognised button. This keeps button handling logic separate from
    command handlers until full features are implemented.
    """
    # Correlation context
    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    if update.effective_user:
        user_id_ctx.set(str(update.effective_user.id))
        telegram_id_ctx.set(str(update.effective_user.id))

    user_id = update.effective_user.id if update.effective_user else "unknown"
    user_input = update.message.text or ""
    logger.info(f"User input from {user_id}: {user_input!r}")

    # Route simple button texts via routing table
    # email verification token pasted?
    if context.user_data.get("awaiting_email_token"):
        token_email = context.user_data["awaiting_email_token"]
        if verify_email_token(token_email, user_input.strip()):
            await update.message.reply_text("✅ E-mail verified! Thank you.")
            cache.get_cached_all_users_data(force=True)
            context.user_data.pop("awaiting_email_token", None)
        else:
            await update.message.reply_text("❌ Token invalid – please try again.")
            context.user_data.pop("awaiting_email_token", None)
            await send_login_menu(update, context)
        return

    if await try_route_text(update, context):
        return


    df_analysis = cache.get_cached_yesterdays_analysis() # This is a pandas dataframe with yesterday's analysis for all tickers
    df_users = cache.get_cached_all_users_data() # This is a pandas dataframe with all users data

    # ---- Check if the user is registered/logged in ---- #
    # ---- ensure user exists in cache ----
    # Guard missing users table/columns (e.g., DB down). Try to detect the telegram id column.
    # The cache now normalizes common telegram id column names to `telegram_user_id`.
    # Use it directly for fast path; detect dynamically only if missing.
    if df_users is None or df_users.empty:
        logger.warning("Users cache unavailable; showing login menu.")
        await send_login_menu(update, context)
        return
    if "telegram_user_id" in df_users.columns:
        mask = df_users["telegram_user_id"].astype(str).str.strip() == str(user_id).strip()
    else:
        mask, _ = _mask_by_telegram_id(df_users, user_id)
        if mask is None:
            logger.warning("Users cache missing telegram id column; showing login menu.")
            await send_login_menu(update, context)
            return
        logger.warning("Users cache unavailable or missing expected columns; showing login menu.")
        await send_login_menu(update, context)
        return
    # Skip while signup or email verification in progress
    if context.user_data.get("signup_in_progress") or context.user_data.get("awaiting_email_token"):
        return

    # Process inventory input
    if inv := context.user_data.pop("awaiting_inventory", None):
        tickers = [t.strip().upper() for t in user_input.split(",") if t.strip()]
        if not tickers:
            await update.message.reply_text("❌ No tickers detected. Try again via Settings → Stocks Inventory.")
            return
        if len(tickers) > inv["allowed"]:
            await update.message.reply_text(
                f"❌ Too many tickers. Your plan allows {inv['allowed']}. Try again.")
            return
        if user_control.update_user_tickers(inv["user_id"], tickers):
            await update.message.reply_text("✅ Inventory updated!")
            cache.get_cached_all_users_data(force=True)
        else:
            await update.message.reply_text("❌ Failed to update inventory. Please retry later.")
        return

    # If user not in cache, force-refresh once
    if not mask.any():
        df_users = cache.get_cached_all_users_data(force=True)
        if df_users is None or df_users.empty:
            await send_login_menu(update, context)
            return
        if "telegram_user_id" in df_users.columns:
            mask = df_users["telegram_user_id"].astype(str).str.strip() == str(user_id).strip()
        else:
            mask, _ = _mask_by_telegram_id(df_users, user_id)
        if mask is None or not mask.any():
            await send_login_menu(update, context)
            return

    user_row = df_users.loc[mask]

    def safe_get(col: str):
        return user_row[col].iloc[0] if col in user_row and not user_row.empty else None

    internal_user_id = safe_get("user_id") or "unknown"
    user_email       = safe_get("email")
    user_plan        = safe_get("plan_type")

    logger.debug("user_row=%s", user_row.to_dict(orient='records'))

    # Route post-authentication button texts (text-based)
    handler = _APP_ROUTES.get(user_input)
    if handler:
        await handler(update, context, internal_user_id, user_id, user_email, user_plan)
        return
    #########################################################################################



def main():
    """Main function to start the Telegram bot."""
    ################################### Check connection to Telegram bot before starting polling ###################################
    bot_token = get("telegram.bot_token_2")
    if not bot_token or "YOUR_TELEGRAM_BOT_TOKEN_2" in bot_token:
        logger.error("Error: Please set your Telegram bot token in the config.")
        return

    ################################### Check if the bot token is valid ###################################
    if not bot_token:
        logger.error("Error: Please set your Telegram bot token in the config.")
        return



    ################################### Check connection to Telegram bot ###################################
    logger.info("Checking connection to Telegram bot...")
    try:
        connected = asyncio.run(check_bot_connection(bot_token))
    except Exception as e:
        logger.error(f"Exception during bot connection check: {e}")
        return

    if not connected:
        logger.error("Bot connection failed. Exiting.")
        return

    ################################### Create a fresh event loop for python-telegram-bot (since asyncio.run closed the default one) ###################################
    asyncio.set_event_loop(asyncio.new_event_loop())
    logger.info("Starting Telegram bot polling...")

    ################################### Start metrics endpoint ###################################
    try:
        metrics_port = int(get("monitoring.metrics_port") or 9100)
    except Exception:
        metrics_port = 9100
    start_metrics_server(metrics_port)

    ################################### Create the bot ###################################
    app = ApplicationBuilder().token(bot_token).build()
    # Global pre-handler to stamp correlation context on every update (messages & callbacks)
    async def _set_log_context(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
        try:
            rid = str(uuid.uuid4())
            request_id_ctx.set(rid)
            if update and update.effective_user:
                user_id_ctx.set(str(update.effective_user.id))
                telegram_id_ctx.set(str(update.effective_user.id))
                username_ctx.set(str(update.effective_user.username or '-'))
            # If user exists in our DB cache, also set internal app user_id
            try:
                df_users_local = cache.get_cached_all_users_data()
                if update and update.effective_user:
                    if df_users_local is not None and not df_users_local.empty and "telegram_user_id" in df_users_local.columns:
                        mask_local = df_users_local["telegram_user_id"].astype(str).str.strip() == str(update.effective_user.id)
                        if mask_local.any():
                            app_user_id_ctx.set(str(df_users_local.loc[mask_local].iloc[0]["user_id"]))
                        else:
                            app_user_id_ctx.set('-')
                    else:
                        app_user_id_ctx.set('-')
            except Exception:
                app_user_id_ctx.set('-')
        except Exception:
            pass

    # Run context-stamping before other handlers
    app.add_handler(MessageHandler(filters.ALL, _set_log_context), group=-1)
    app.add_handler(CallbackQueryHandler(_set_log_context), group=-1)


    ################################### Add the handlers ###################################
    app.add_handler(CommandHandler("start", start))
    # Register static text routes as separate handlers (Regex) so they short-circuit early
    register_text_routes(app)

    # Inline menu handlers (callback queries)
    async def handle_inline_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        data = query.data or ""
        await query.answer()
        internal_user_id, user_id, user_email, user_plan = await _get_user_context(update)
        if data == "menu:stock":
            await _handle_stock_analysis(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "menu:graphs":
            await _handle_graphs(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "menu:settings":
            await _handle_settings(update, context, internal_user_id, user_id, user_email, user_plan)

    app.add_handler(CallbackQueryHandler(handle_inline_menu, pattern=r"^menu:(stock|graphs|settings)$"))

    async def handle_inline_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        data = query.data or ""
        await query.answer()
        if data == "auth:login":
            await login_start(update, context)
        elif data == "auth:signup":
            await signup_start(update, context)
        elif data == "auth:forgot":
            await forgot_start(update, context)

    app.add_handler(CallbackQueryHandler(handle_inline_login, pattern=r"^auth:(login|signup|forgot)$"))

    async def handle_inline_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        data = query.data or ""
        await query.answer()
        internal_user_id, user_id, user_email, user_plan = await _get_user_context(update)
        if data == "settings:inventory":
            await _handle_stocks_inventory(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "settings:weights":
            await _handle_stock_weights(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "settings:user":
            await _handle_user_details(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "settings:login":
            await _handle_login_signup(update, context, internal_user_id, user_id, user_email, user_plan)
        elif data == "settings:payments":
            await _handle_payments(update, context, internal_user_id, user_id, user_email, user_plan)

    app.add_handler(CallbackQueryHandler(handle_inline_settings, pattern=r"^settings:(inventory|weights|user|login|payments)$"))

    # Login conversation handler
    conv_login = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔑 Login$"), login_start)],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_login)


    # Sign-up conversation handler
    conv_signup = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✨ Sign Up$"), signup_start)],
        states={
            SIGNUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup_name)],
            SIGNUP_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup_email)],
            SIGNUP_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup_password)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_signup)

    # Forgot-password conversation handler
    conv_forgot = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔄 Forgot my password$"), forgot_start)],
        states={
            FORGOT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, forgot_email)],
            FORGOT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, forgot_password)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_forgot)

    # Add the fallback handler with lowest priority (after command and echo handlers)
    app.add_handler(MessageHandler(filters.ALL, fallback_handler), group=1)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitored_echo))

    # Callback handler for stock analysis inline buttons
   
    app.add_handler(CallbackQueryHandler(stock_analysis.handle_callback, pattern=r"^sa_(ticker:|back$)"))
    app.add_handler(CallbackQueryHandler(graphs_menu.handle_graphs_callback, pattern=r"^gm_(example:|back$)"))

    # Schedule daily cache refresh at 06:00 server time
    app.job_queue.run_daily(
        lambda ctx: cache.get_cached_yesterdays_analysis(force=True),
        time=dtime(hour=6, minute=0),
        name="refresh_yesterdays_analysis"
    )

    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        app.run_polling()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Error running the bot: {e}")


if __name__ == "__main__":
    main()









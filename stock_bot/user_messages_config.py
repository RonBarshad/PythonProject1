from telegram import InlineKeyboardMarkup, InlineKeyboardButton




# ---------------------------------------------------------------------------
#  Menu
# ---------------------------------------------------------------------------
MENU_MESSAGE = (
    "Please choose an option below:\n"
    "• 📈 Stock Analysis: Get Your daily stock analysis.\n"
    "• 📊 Graphs: View interactive price and technical indicator charts.\n"
    "• ⚙️ Settings: Configure your preferences and payments."
)


def get_menu_message_and_keyboard():
    """
    Returns the menu message and an InlineKeyboardMarkup with three buttons:
    Stock Analysis, Graphs, Settings.
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="📈 Stock Analysis", callback_data="menu:stock"),
            InlineKeyboardButton(text="📊 Graphs", callback_data="menu:graphs"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings"),
        ]
    ])
    return MENU_MESSAGE, keyboard


# ---------------------------------------------------------------------------
#  Login menu
# ---------------------------------------------------------------------------
LOGIN_MESSAGE = (
    "Please choose an option below:\n"
    "• 🔑 Login: Login to your account.\n"
    "• ✨ Sign Up: Create a new account.\n"
    "• 🔄 Forgot my password: Reset your password."
)

def get_login_message_and_keyboard():
    """
    Returns the login message and an InlineKeyboardMarkup with three buttons:
    Login, Sign Up, Forgot my password.
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="🔑 Login", callback_data="auth:login"),
            InlineKeyboardButton(text="✨ Sign Up", callback_data="auth:signup"),
            InlineKeyboardButton(text="🔄 Forgot my password", callback_data="auth:forgot"),
        ]
    ])
    return LOGIN_MESSAGE, keyboard


# ---------------------------------------------------------------------------
#  Settings menu
# ---------------------------------------------------------------------------
SETTINGS_MESSAGE = (
    "Please choose an option below:\n"
    "• 📋 Stocks Inventory: View and manage your stock portfolio.\n"
    "• ⚖️ Stock Weights: Adjust portfolio allocation weights.\n" 
    "• 👤 User Details: Update your account information.\n"
    "• 🔄 Login/Signup: Login to your account or sign up for a new account.\n"
    "• 💰 Payments: View and manage your payments."
)


def get_settings_message_and_keyboard():
    """
    Returns the settings message and an InlineKeyboardMarkup with buttons.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="📋 Stocks Inventory", callback_data="settings:inventory")],
        [InlineKeyboardButton(text="⚖️ Stock Weights", callback_data="settings:weights")],
        [InlineKeyboardButton(text="👤 User Details", callback_data="settings:user")],
        [InlineKeyboardButton(text="🔄 Login/Signup", callback_data="settings:login")],
        [InlineKeyboardButton(text="💰 Payments", callback_data="settings:payments")],
    ])
    return SETTINGS_MESSAGE, keyboard


# ---------------------------------------------------------------------------
#  Welcome message
# ---------------------------------------------------------------------------
WELCOME_MESSAGE = (
    "Hello! 👋\n"
    "I am your stock analysis bot. Send me a stock ticker (e.g., AAPL, NVDA) or ask me about the market, "
    "and I'll provide you with the latest AI-powered analysis, technical insights, and news summaries.\n\n"
    "Type /help for more info or just send a message to get started!"
)



def get_welcome_message():
    """Return the welcome message for new users."""
    return WELCOME_MESSAGE


# ---------------------------------------------------------------------------
#  Stocks analysis
# ---------------------------------------------------------------------------








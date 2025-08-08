# Stock Analysis Telegram Bot

This directory contains the new experimental Telegram bot that delivers AI-powered stock analysis, interactive price charts and basic portfolio utilities.

| Feature | Status |
|---------|--------|
| `/start` + welcome message | ✅ |
| Main menu with reply-keyboard (Stock Analysis, Graphs, Settings) | ✅ |
| User authentication (`/signup`, `/login`, `/forgot`) | ✅ |
| Automatic login / sign-up prompt for unregistered users | ✅ |
| Stock-analysis inline flow (protected) | ✅ |
| Settings submenu | 🛠️ in progress |

---

## 1. Quick start

```bash
# From the project root, activate your virtual-env first
(.venv) $ cd PythonProject1

# Install python-telegram-bot if missing
pip install python-telegram-bot==20.*

# Run the bot (package style – recommended)
python -m stock_bot.main

# or run the script directly
python stock_bot/main.py
```

> **Tip:** Running with `python -m stock_bot.main` automatically adds the project root to `PYTHONPATH`, avoiding import problems.

---

## 2. Required environment variables

The bot expects its credentials in your `.env` file or in the OS environment. The config loader (`config/config.py`) reads them automatically on import via `python-dotenv`.

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN_2` | Token for the _second_ Telegram bot (this experimental one) |

Example `.env`:

```dotenv
TELEGRAM_BOT_TOKEN_2=123456:ABC-DEF…
```

If you deploy to Heroku / Render / Railway, set the variable in the dashboard instead of a `.env` file.

---

## 3. Code structure

```
stock_bot/
├── main.py                 # Entry-point – sets up handlers & runs polling
├── user_messages_config.py # Centralised texts + keyboard layouts
└── README.md               # You are here
```

### 3.1 `main.py`

Handles:

* `/start` command → sends welcome + menu.
* `monitored_echo` → intercepts text messages, logs the input and routes recognised menu buttons to stub handlers.
* `fallback_handler` → when input is unknown, show the menu again.
* Safe startup: verifies bot token, tests the connection (`check_bot_connection`), then starts polling.

### 3.2 `user_messages_config.py`

Keeps all user-facing strings and `ReplyKeyboardMarkup` definitions in one place so translators / copywriters can update texts without touching bot logic.

### 3.3 `user_control.py`

Centralised helpers for user management (no Telegram dependency):

* `sign_up(full_name, email, password, telegram_user_id)` – create user row with hashed password.
* `sign_in(email, password)` – validate credentials & update `last_login`.
* `forgot_password(email, new_password)` – update password + audit fields.
* `authenticate_via_telegram(telegram_user_id)` – mark DB row as verified via Telegram.
* `requires_relogin(last_login, days=10)` – check if user must sign-in again.

`main.py` exposes bot commands `/signup`, `/login`, `/forgot` that call these helpers.

**Automatic prompt**  
If someone sends a message but is **not** found in the users-data cache the bot now:
1. Displays a small keyboard with three buttons: *Login*, *Sign&nbsp;Up*, *Forgot my password*.
2. Explains which slash-command to use after the button tap.

This makes onboarding easier and avoids sending lengthy instructions manually.

---

## 4. Stock Analysis – inline flow (protected)

The "📈 Stock Analysis" button now opens an inline menu inside the chat (not the reply keyboard):

- Last daily update timestamp is shown (based on cached DB data)
- User's configured tickers are shown as inline buttons
- A "⬅️ Back to Menu" button returns to the main menu

When tapping a ticker, the bot sends the latest analysis text for that ticker from `cache.get_cached_yesterdays_analysis()` (column `text_analysis`). The message is sent with `protect_content=True`, so it cannot be copied or forwarded.

Entrypoints:

- `stock_bot/stock_analysis.py` – flow implementation
- `stock_bot/main.py` – routes "📈 Stock Analysis" to `show_stock_analysis_menu(...)` and registers a `CallbackQueryHandler` for `sa_ticker:*` and `sa_back`.

Data source and caching:

- `stock_bot/cache.py` provides `get_cached_yesterdays_analysis()` which returns a pandas DataFrame of yesterday’s analyses.
- Cache refresh runs daily at 06:00 via JobQueue; can also be forced with `force=True`.

Button privacy:

- Analysis messages use `protect_content=True` and `disable_web_page_preview=True`.

---

## 5. Extending functionality

1. **Add new menu buttons** – edit `MENU_BUTTONS` in `user_messages_config.py` and update `monitored_echo` routing.
2. **Implement real stock analysis** – replace the placeholder reply in the `"📈 Stock Analysis"` branch with the actual logic from existing modules (`ai/*`, `data_processing/*`).
3. **Graphs** – integrate `matplotlib` or a chart API and send images back to the user.
4. **Settings** – create a small FSM (finite-state machine) or use `ConversationHandler` to let users toggle options stored in the DB.

---

## 6. Background services (Docker)

Two independent services run on schedules via Docker Compose:

- `stock-scheduler` – daily jobs
  - 05:00: raw data ingestion for all `tickers`
  - 06:00: self-AI analysis for all `tickers` (yesterday), then cache refresh
- `stock-mailer` – daily email
  - 07:00: send stock analysis emails with inline charts to recipients in config

Configure recipients and timing in `config/config.json` under `email`:

```json
"email": {
  "recipients": ["user@example.com"],
  "hour": 7,
  "minute": 0,
  "days": 60
}
```

To start only the services:

```bash
docker compose up -d --build stock-scheduler stock-mailer
```

Logs are shipped to Loki (if enabled) and visible in Grafana via labels `service="stock-scheduler"` and `service="stock-mailer"`.

---

## 7. Daily cache of yesterday's analysis

To minimise database load the bot caches the **self_ai_analysis_ticker** query in RAM.

* On startup it performs an initial fetch via `cache.get_cached_yesterdays_analysis(force=True)`.
* A background job in python-telegram-bot’s `JobQueue` refreshes the cache every day at **06:00** server time.
* Handlers access the data with
  ```python
  from stock_bot import cache
  df = cache.get_cached_yesterdays_analysis()  # cheap, automatically up-to-date
  ```

If you ever need to force-update (e.g., admin command) call the same helper with `force=True`.

---

## 8. Logging

`logging` is configured at INFO level. Telegram HTTP requests (via `httpx`) are visible too. For debugging, switch the level to `DEBUG` in `main.py`.

---

## 9. Known issues / TODO

* Event-loop handling is a bit verbose due to the pre-startup token check; consider refactoring when async start-up helpers are available in python-telegram-bot.
* Only a single worker process is assumed. For production, run multiple dynos/processes behind a queue or switch to webhooks.
* Feature stubs need proper implementations.

Feel free to open issues or PRs to improve this bot!

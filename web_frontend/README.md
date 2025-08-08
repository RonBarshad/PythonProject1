Web Frontend (Flask)

Quick start (local):

1) Install deps at repo root:

   Windows PowerShell
   - python -m venv .venv
   - .\.venv\Scripts\Activate.ps1
   - pip install -r requirements.txt

2) Create .env in repo root (optional but recommended):

   WEB_SESSION_SECRET=change-me

3) Run the app:

   python web_frontend/app.py

4) Open http://localhost:8000

Pages:
- /               Home
- /pricing        Pricing
- /about          About Us
- /login          Login
- /signup         Sign up
- /dashboard      Dashboard (after login)

Docker (optional):

- docker compose up web-frontend -d
- Open http://localhost:8000

Notes:
- Authentication reuses functions in `stock_bot/user_control.py`. Ensure DB config is valid in `config/config.json` or via environment variables.
- Telegram bot shortcut: /go-telegram or the header button. 


from __future__ import annotations

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
import os
import sys
from pathlib import Path

# Ensure project root is importable when running this file directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse existing user management logic
from stock_bot import user_control


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("WEB_SESSION_SECRET", "dev-secret-change-me")
    app.permanent_session_lifetime = timedelta(days=7)

    telegram_bot_url = "https://t.me/stock_analysis_1234bot"

    @app.context_processor
    def inject_globals():
        return {
            "telegram_bot_url": telegram_bot_url
        }

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/pricing")
    def pricing():
        return render_template("pricing.html")

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "GET":
            return render_template("signup.html")
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not full_name or not email or not password:
            flash("Please fill all fields", "error")
            return redirect(url_for("signup"))
        ok = user_control.sign_up(full_name, email, password)
        if ok:
            flash("Sign-up successful. Please login.", "success")
            return redirect(url_for("login"))
        flash("User already exists or an error occurred.", "error")
        return redirect(url_for("signup"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Please provide e-mail and password", "error")
            return redirect(url_for("login"))
        ok = user_control.sign_in(email, password)
        if ok:
            user = user_control.get_user_by_email(email)
            session.permanent = True
            session["user_id"] = user.get("user_id") if user else None
            session["email"] = email
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Wrong email or password.", "error")
        return redirect(url_for("login"))

    @app.get("/logout")
    def logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("home"))

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect(url_for("login"))
        user = None
        if session.get("email"):
            user = user_control.get_user_by_email(session["email"]) or {}
        return render_template("dashboard.html", user=user)

    @app.get("/go-telegram")
    def go_telegram():
        return redirect(telegram_bot_url)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    create_app().run(host="0.0.0.0", port=port, debug=True)



"""
notifications/email_sender.py
Mission: Send email messages to users. This module connects to an SMTP server and can send emails to users by their email address.

Requirements:
- Set your SMTP server, port, sender email, and password in environment variables or config.
- The recipient email must be a valid email address.

Usage:
    python notifications/email_sender.py
"""

import smtplib
from email.message import EmailMessage
import mysql.connector
from datetime import datetime, timedelta
from config.config import get
import json

# SMTP configuration (set these as environment variables or replace with your values)
SMTP_SERVER = get("smtp_server")
SMTP_PORT = get("smtp_port")
SMTP_USER = get("smtp_user")
SMTP_PASSWORD = get("smtp_password")
SENDER_EMAIL = SMTP_USER


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    """
    Send an email to a user.
    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The email subject.
        body (str): The email body (plain text).
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def get_yesterdays_ticker_analyses_for_user(email: str):
    """
    Pull all relevant data about yesterday's tickers related to a user's email.
    Args:
        email (str): The user's email address.
    Returns:
        List of (ticker, analysis_text) tuples for yesterday.
    """
    # Get DB credentials
    creds = {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        # 1. Get user's tickers
        cursor.execute("SELECT tickers FROM fact_users_data_table WHERE email=%s", (email,))
        row = cursor.fetchone()
        if not row or not row[0]:
            print(f"No tickers found for user {email}")
            return []
        tickers_str = str(row[0])
        tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
        # 2. For each ticker, get yesterday's analysis
        yesterday = (datetime.now() - timedelta(days=1)).date()
        results = []
        for ticker in tickers:
            cursor.execute(
                """
                SELECT text_analysis, grade FROM self_ai_analysis_ticker
                WHERE company_ticker=%s AND analysis_event_date=%s and test_ind=0
                ORDER BY insertion_time DESC LIMIT 1
                """,
                (ticker, yesterday)
            )
            analysis_row = cursor.fetchone()
            if analysis_row and analysis_row[0]:
                results.append((ticker, analysis_row[0], analysis_row[1]))
        return results
    except Exception as e:
        print(f"DB error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()




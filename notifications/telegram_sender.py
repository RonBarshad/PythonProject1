"""
notifications/telegram_sender.py
Mission: Send messages to users via Telegram. This module connects to the Telegram Bot API and can send messages to users by their Telegram user_id.

Requirements:
- Set your Telegram bot token in the TELEGRAM_BOT_TOKEN environment variable or config.
- The user_id must be the Telegram chat/user ID (not your internal user_id).

Usage:
    python notifications/telegram_sender.py
"""

import os
from telegram import Bot

# You can set your bot token here or use an environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "<YOUR_TELEGRAM_BOT_TOKEN>")

# The Telegram user/chat ID to send the message to (must be an integer for Telegram)
TELEGRAM_USER_ID = 426dbe3015f34e0cbeffc4418198b809  # Replace with the actual Telegram chat/user ID (integer)


def send_telegram_message(user_id: int, message: str) -> bool:
    """
    Send a message to a Telegram user via the bot.
    Args:
        user_id (int): Telegram chat/user ID.
        message (str): The message to send.
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=user_id, text=message)
        print(f"Message sent to {user_id}")
        return True
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False


if __name__ == "__main__":
    # Test: send 'hello' to the user
    # NOTE: Replace TELEGRAM_USER_ID with the actual integer Telegram chat/user ID
    print("Sending test message via Telegram...")
    send_telegram_message(TELEGRAM_USER_ID, "hello") 
"""
notifications/telegram_sender.py
Mission: Send messages to users via Telegram Bot.

Requirements:
- Bot token from @BotFather
- User ID to send messages to

Usage:
    python notifications/telegram_sender.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon import TelegramClient
from config.config import get
import asyncio

# Get Telegram configuration from config
APP_ID = get("telegram.app_id")
API_HASH = get("telegram.api_hash")
BOT_TOKEN = get("telegram.bot_token")
BOT_NAME = get("telegram.bot_name")
BOT_USERNAME = get("telegram.bot_username")
TELEGRAM_USER_ID = get("telegram.user_id")


async def send_hello(user_id: int) -> bool:
    """
    Send a simple "hello" message using the Telegram bot.
    
    Args:
        user_id (int): Telegram user ID to send message to
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not BOT_TOKEN:
        print("❌ Bot token not configured!")
        return False
    
    print(f"🤖 Using bot: {BOT_NAME} (@{BOT_USERNAME})")
    print(f"👤 Sending to user ID: {user_id}")
    
    # Create client
    client = TelegramClient('bot_session', APP_ID, API_HASH)
    
    try:
        # Start the client with bot token
        await client.start(bot_token=BOT_TOKEN)
        
        # Send hello message
        await client.send_message(entity=user_id, message="Hello! 👋")
        
        print("✅ Hello message sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False
    finally:
        await client.disconnect()


def send_hello_sync(user_id: int) -> bool:
    """
    Synchronous wrapper for send_hello.
    """
    return asyncio.run(send_hello(user_id))


async def get_bot_info() -> None:
    """
    Get information about the bot and test connection.
    """
    if not BOT_TOKEN:
        print("❌ Bot token not configured!")
        return
    
    print(f"🤖 Bot: {BOT_NAME} (@{BOT_USERNAME})")
    
    client = TelegramClient('bot_session', APP_ID, API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        
        # Get bot info
        me = await client.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"📱 Bot ID: {me.id}")
        print(f"📝 Bot Name: {me.first_name}")
        print(f"🔗 Bot Username: @{me.username}")
        
        # Get updates (messages sent to bot)
        updates = await client.get_messages('me', limit=5)
        if updates:
            print(f"\n📨 Recent messages to bot:")
            for msg in updates:
                if msg.sender_id:
                    print(f"   From User ID: {msg.sender_id}")
        else:
            print(f"\n📨 No recent messages found.")
            print(f"   💡 Send a message to @{BOT_USERNAME} to start the bot!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    print("🚀 Starting Telegram Bot Test...")
    
    # First, get bot info and check for users
    print("\n📊 Getting bot information...")
    asyncio.run(get_bot_info())
    
    print("\n📤 Testing hello message...")
    # Test sending hello
    success = send_hello_sync(TELEGRAM_USER_ID)
    
    if success:
        print("🎉 Bot is working perfectly!")
    else:
        print("💥 Bot test failed!")
        print("\n💡 To fix this:")
        print("   1. Open Telegram")
        print("   2. Search for @Ronfirstbot")
        print("   3. Click 'Start' or send /start")
        print("   4. Run this script again")


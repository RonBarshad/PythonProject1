#!/usr/bin/env python3
"""
Test script for Telegram bot functionality
"""

import asyncio
from notifications.telegram_sender import StockBot

async def test_bot():
    """Test the bot functionality"""
    print("🤖 Testing Telegram Bot...")
    
    # Create bot instance
    bot = StockBot()
    
    # Test input validation
    print("\n✅ Testing input validation:")
    test_inputs = [
        "AAPL",           # Valid ticker
        "Hello there!",   # Valid greeting
        "Thanks!",        # Valid thank you
        "AAPL RSI",       # Valid ticker with extra text
        "<script>alert('xss')</script>",  # Invalid - contains script
        "A" * 200,        # Invalid - too long
        "",               # Invalid - empty
    ]
    
    for test_input in test_inputs:
        is_valid = bot._is_valid_input(test_input)
        print(f"  '{test_input[:20]}...' -> {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test ticker extraction
    print("\n✅ Testing ticker extraction:")
    test_messages = [
        "I want to see AAPL analysis",
        "What about MSFT?",
        "Show me GOOGL",
        "Hello there",
        "Thanks for the help",
        "NVDA is doing well",
        "TSLA analysis please"
    ]
    
    for message in test_messages:
        ticker = bot._extract_ticker_from_message(message)
        print(f"  '{message}' -> '{ticker}'")
    
    print("\n✅ Bot test completed!")

if __name__ == "__main__":
    asyncio.run(test_bot()) 
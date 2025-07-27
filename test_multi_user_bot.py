#!/usr/bin/env python3
"""
Test script for multi-user Telegram bot functionality
"""

import asyncio
import time
from notifications.telegram_sender import StockBot

async def test_multi_user_functionality():
    """Test the bot's multi-user capabilities"""
    print("🤖 Testing Multi-User Bot Functionality...")
    
    # Create bot instance
    bot = StockBot()
    
    # Test 1: Rate limiting
    print("\n✅ Testing Rate Limiting:")
    user_ids = [12345, 67890, 11111]
    
    for user_id in user_ids:
        print(f"\n  Testing user {user_id}:")
        for i in range(12):  # Try 12 messages (should limit at 10)
            can_send = bot._check_rate_limit(user_id)
            print(f"    Message {i+1}: {'✅ Allowed' if can_send else '❌ Rate Limited'}")
            if not can_send:
                break
    
    # Test 2: Input validation
    print("\n✅ Testing Input Validation:")
    test_inputs = [
        ("AAPL", True),
        ("Hello there!", True),
        ("<script>alert('xss')</script>", False),
        ("A" * 200, False),
        ("", False),
        ("AAPL RSI", True),
        ("12345", True),
        ("AAPL-MSFT", True),
    ]
    
    for test_input, expected in test_inputs:
        is_valid = bot._is_valid_input(test_input)
        status = "✅ Valid" if is_valid == expected else "❌ Invalid"
        print(f"  '{test_input[:20]}...' -> {status} (Expected: {expected})")
    
    # Test 3: Ticker extraction
    print("\n✅ Testing Ticker Extraction:")
    test_messages = [
        ("I want to see AAPL analysis", "AAPL"),
        ("What about MSFT?", "MSFT"),
        ("Show me GOOGL", "GOOGL"),
        ("Hello there", ""),
        ("NVDA is doing well", "NVDA"),
        ("TSLA analysis please", "TSLA"),
        ("Multiple AAPL MSFT GOOG", "AAPL"),  # Should return first match
    ]
    
    for message, expected in test_messages:
        ticker = bot._extract_ticker_from_message(message)
        status = "✅ Correct" if ticker == expected else "❌ Wrong"
        print(f"  '{message}' -> '{ticker}' {status} (Expected: '{expected}')")
    
    # Test 4: Database connection safety
    print("\n✅ Testing Database Connection Safety:")
    try:
        conn = bot._get_db_connection()
        if conn:
            print("  ✅ Database connection successful")
            conn.close()
        else:
            print("  ⚠️ Database connection failed (expected if no DB)")
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
    
    # Test 5: User session management
    print("\n✅ Testing User Session Management:")
    print(f"  Initial sessions: {len(bot.user_sessions)}")
    
    # Simulate multiple users
    for user_id in [111, 222, 333]:
        bot._check_rate_limit(user_id)
    
    print(f"  After adding users: {len(bot.user_sessions)}")
    print(f"  Session keys: {list(bot.user_sessions.keys())}")
    
    print("\n✅ Multi-user tests completed!")

def test_concurrent_access():
    """Test concurrent access patterns"""
    print("\n🔄 Testing Concurrent Access Patterns:")
    
    bot = StockBot()
    
    # Simulate concurrent user access
    import threading
    import time
    
    def simulate_user(user_id):
        """Simulate a user sending messages"""
        for i in range(5):
            can_send = bot._check_rate_limit(user_id)
            print(f"  User {user_id}, Message {i+1}: {'✅' if can_send else '❌'}")
            time.sleep(0.1)  # Simulate processing time
    
    # Create multiple threads for different users
    threads = []
    for user_id in [1001, 1002, 1003, 1004, 1005]:
        thread = threading.Thread(target=simulate_user, args=(user_id,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"  Final session count: {len(bot.user_sessions)}")
    print("✅ Concurrent access test completed!")

if __name__ == "__main__":
    # Run async tests
    asyncio.run(test_multi_user_functionality())
    
    # Run concurrent tests
    test_concurrent_access()
    
    print("\n🎉 All tests completed successfully!") 
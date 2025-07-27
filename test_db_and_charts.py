#!/usr/bin/env python3
"""
Test script for database connection and chart generation
"""

import asyncio
from notifications.telegram_sender import StockBot

async def test_database_and_charts():
    """Test database connection and chart generation"""
    print("🧪 Testing Database Connection and Chart Generation...")
    
    # Create bot instance
    bot = StockBot()
    
    # Test 1: Database connection
    print("\n✅ Testing Database Connection:")
    try:
        conn = bot._get_db_connection()
        if conn:
            print("  ✅ Database connection successful")
            conn.close()
        else:
            print("  ❌ Database connection failed")
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
    
    # Test 2: Get analysis from database
    print("\n✅ Testing Analysis Retrieval:")
    test_tickers = ["AAPL", "NVDA", "IONQ"]
    
    for ticker in test_tickers:
        try:
            analysis_data = bot._get_latest_analysis_from_db(ticker)
            if analysis_data:
                analysis_text, grade = analysis_data
                print(f"  ✅ {ticker}: Found analysis (Grade: {grade})")
                print(f"     Text preview: {analysis_text[:100]}...")
            else:
                print(f"  ⚠️ {ticker}: No analysis found in database")
        except Exception as e:
            print(f"  ❌ {ticker}: Error retrieving analysis - {e}")
    
    # Test 3: Chart generation
    print("\n✅ Testing Chart Generation:")
    for ticker in test_tickers:
        try:
            from graphs.candlestick_chart import generate_candlestick_chart
            chart_data = generate_candlestick_chart(ticker, 60)
            if chart_data:
                print(f"  ✅ {ticker}: Chart generated successfully ({len(chart_data)} bytes)")
            else:
                print(f"  ❌ {ticker}: Chart generation failed")
        except Exception as e:
            print(f"  ❌ {ticker}: Chart generation error - {e}")
    
    # Test 4: Complete analysis flow
    print("\n✅ Testing Complete Analysis Flow:")
    for ticker in test_tickers[:1]:  # Test with first ticker only
        try:
            analysis = await bot._get_ticker_analysis(ticker)
            if analysis and "❌" not in analysis:
                print(f"  ✅ {ticker}: Complete analysis successful")
                print(f"     Preview: {analysis[:200]}...")
            else:
                print(f"  ❌ {ticker}: Analysis failed")
        except Exception as e:
            print(f"  ❌ {ticker}: Analysis error - {e}")
    
    print("\n🎉 Database and Chart tests completed!")

if __name__ == "__main__":
    asyncio.run(test_database_and_charts()) 
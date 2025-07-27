#!/usr/bin/env python3
"""
Test script for analysis formatting
"""

from notifications.telegram_sender import StockBot

def test_analysis_formatting():
    """Test the analysis formatting function"""
    print("🧪 Testing Analysis Formatting...")
    
    # Create bot instance
    bot = StockBot()
    
    # Test raw analysis text with different sections
    test_analysis = """
    <TA>Technical analysis shows strong momentum with RSI at 65 and MACD positive. Price is above 20-day SMA.</TA>
    <CN>Company reported strong Q4 earnings with 15% revenue growth. New product launch announced.</CN>
    <WN>Global markets showing positive sentiment. Fed policy remains accommodative.</WN>
    <IC>Industry experiencing consolidation. Competitors launching similar products.</IC>
    <COMP>Main competitors are MSFT and GOOGL. Market share stable at 25%.</COMP>
    <LEGAL>No significant legal issues reported. All regulatory filings up to date.</LEGAL>
    <FIN>Strong balance sheet with $50B cash reserves. Debt-to-equity ratio at 0.3.</FIN>
    """
    
    print("\n📝 Original Analysis Text:")
    print(test_analysis)
    
    print("\n✨ Formatted Analysis Text:")
    formatted = bot._format_analysis_text_for_display(test_analysis)
    print(formatted)
    
    # Test with missing sections
    print("\n📝 Test with Missing Sections:")
    partial_analysis = """
    <TA>Technical indicators are mixed. RSI at 45, neutral territory.</TA>
    <CN>No significant company news this week.</CN>
    """
    
    formatted_partial = bot._format_analysis_text_for_display(partial_analysis)
    print(formatted_partial)
    
    # Test with no sections
    print("\n📝 Test with No Sections:")
    plain_analysis = "This is a plain analysis without any sections."
    
    formatted_plain = bot._format_analysis_text_for_display(plain_analysis)
    print(formatted_plain)
    
    print("\n✅ Formatting tests completed!")

if __name__ == "__main__":
    test_analysis_formatting() 
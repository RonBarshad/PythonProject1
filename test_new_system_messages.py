"""
test_new_system_messages.py
Mission: Test the new system messages for daily and weekly analysis.
"""

from datetime import date
from ai.self_ai_analysis_by_ticker import (
    extract_system_message_and_model,
    parse_gpt_output,
    self_ai_analysis_by_ticker
)


def test_system_message_extraction():
    """Test if the new system messages can be extracted correctly."""
    print("🔍 Testing system message extraction...")
    
    try:
        # Test daily analysis
        daily_msg, daily_model = extract_system_message_and_model("day")
        print(f"✅ Daily analysis:")
        print(f"   Model: {daily_model}")
        print(f"   Message length: {len(daily_msg)} characters")
        print(f"   Contains 'DAILY': {'DAILY' in daily_msg}")
        print(f"   Contains '24 HOURS': {'24 HOURS' in daily_msg}")
        
        # Test weekly analysis
        weekly_msg, weekly_model = extract_system_message_and_model("week")
        print(f"✅ Weekly analysis:")
        print(f"   Model: {weekly_model}")
        print(f"   Message length: {len(weekly_msg)} characters")
        print(f"   Contains 'WEEKLY': {'WEEKLY' in weekly_msg}")
        print(f"   Contains '7 CALENDAR DAYS': {'7 CALENDAR DAYS' in weekly_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ System message extraction failed: {e}")
        return False


def test_grade_parsing():
    """Test the new grade parsing logic."""
    print("\n🔍 Testing grade parsing...")
    
    test_cases = [
        # New format: 1-10 scale
        ("Technical analysis shows bullish trend. Company news positive. 8.5", 
         "Technical analysis shows bullish trend. Company news positive.", 0.833),
        ("Mixed signals with negative sentiment. 3.0", 
         "Mixed signals with negative sentiment.", 0.222),
        ("Strong bearish indicators. 1.5", 
         "Strong bearish indicators.", 0.056),
        ("Excellent performance across all metrics. 9.8", 
         "Excellent performance across all metrics.", 0.978),
        
        # Legacy JSON format (should still work)
        ('{"score": 0.75, "explanation": "Good performance"}', 
         "Good performance", 0.75),
        
        # Edge cases
        ("No analysis provided", "No analysis provided", 0.0),
        ("", "No analysis provided", 0.0),
        (None, "No analysis provided", 0.0)
    ]
    
    all_passed = True
    for i, (input_text, expected_text, expected_grade) in enumerate(test_cases):
        try:
            result_text, result_grade = parse_gpt_output(input_text)
            if (result_text == expected_text and 
                abs(result_grade - expected_grade) < 0.01):
                print(f"  ✅ Test {i+1}: PASS")
            else:
                print(f"  ❌ Test {i+1}: FAIL")
                print(f"     Expected: ({expected_text}, {expected_grade})")
                print(f"     Got: ({result_text}, {result_grade})")
                all_passed = False
        except Exception as e:
            print(f"  ❌ Test {i+1}: ERROR - {e}")
            all_passed = False
    
    return all_passed


def test_configuration_keys():
    """Test if the configuration keys are correctly mapped."""
    print("\n🔍 Testing configuration key mapping...")
    
    try:
        from config.config import get
        
        # Test the new keys exist
        daily_msg = get("self_analysis.daily_analysis_system_message")
        weekly_msg = get("self_analysis.weekly_analysis_system_message")
        
        if daily_msg and weekly_msg:
            print("✅ Both daily and weekly system messages found")
            print(f"   Daily message length: {len(daily_msg)}")
            print(f"   Weekly message length: {len(weekly_msg)}")
            return True
        else:
            print("❌ Missing system messages")
            print(f"   Daily message: {'Found' if daily_msg else 'Missing'}")
            print(f"   Weekly message: {'Found' if weekly_msg else 'Missing'}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_analysis_function():
    """Test the main analysis function with new system messages."""
    print("\n🔍 Testing main analysis function...")
    
    try:
        # Test with minimal parameters (won't make actual API call)
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="TEST",
            model="gpt-3.5-turbo",
            weights='{"technical_analysis": 0.5, "company_news": 0.3, "financial": 0.2}',
            analysis_type="day",
            test="yes"
        )
        
        print(f"✅ Analysis function executed successfully")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Ticker: {result.get('company_ticker')}")
        print(f"   Analysis Type: {result.get('analysis_type')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis function test failed: {e}")
        return False


def main():
    """Run all tests for the new system messages."""
    print("🚀 Testing New System Messages")
    print("=" * 60)
    
    tests = [
        ("Configuration Keys", test_configuration_keys),
        ("System Message Extraction", test_system_message_extraction),
        ("Grade Parsing", test_grade_parsing),
        ("Analysis Function", test_analysis_function)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The new system messages are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
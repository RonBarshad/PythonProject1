"""
test_self_ai_analysis.py
Mission: Test script to verify the self_ai_analysis_by_ticker functionality.
"""

from datetime import date
from ai.self_ai_analysis_by_ticker import self_ai_analysis_by_ticker, run_analysis_example


def test_basic_functionality():
    """
    Mission: Test the basic functionality of self_ai_analysis_by_ticker.
    """
    print("=" * 60)
    print("Testing Self AI Analysis by Ticker")
    print("=" * 60)
    
    # Test parameters
    analysis_event_date = date.today()
    company_ticker = "AAPL"
    model = "gpt-3.5-turbo"
    weights = '{"technical_analysis": 0.35, "company_news": 0.25, "world_news": 0.10}'
    analysis_type = "day"
    test = "yes"  # Use test mode
    
    print(f"Analysis Event Date: {analysis_event_date}")
    print(f"Company Ticker: {company_ticker}")
    print(f"Model: {model}")
    print(f"Weights: {weights}")
    print(f"Analysis Type: {analysis_type}")
    print(f"Test Mode: {test}")
    print("-" * 60)
    
    # Run the analysis
    result = self_ai_analysis_by_ticker(
        analysis_event_date=analysis_event_date,
        company_ticker=company_ticker,
        model=model,
        weights=weights,
        analysis_type=analysis_type,
        test=test
    )
    
    # Display results
    print("\nResults:")
    print("-" * 30)
    if result['success']:
        print(f"✅ Analysis completed successfully!")
        print(f"📊 Grade: {result['grade']}")
        print(f"📝 Text Analysis: {result['text_analysis']}")
        print(f"🤖 Model Used: {result['model']}")
        print(f"🔢 Tokens Used: {result['prompt_tokens'] + result['execution_tokens']}")
        print(f"📅 Analysis Date: {result['analysis_event_date']}")
        print(f"🧪 Test Mode: {'Yes' if result['test_ind'] else 'No'}")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
    
    return result


def test_week_analysis():
    """
    Mission: Test week analysis functionality.
    """
    print("\n" + "=" * 60)
    print("Testing Week Analysis")
    print("=" * 60)
    
    # Test parameters for week analysis
    analysis_event_date = date.today()
    company_ticker = "MSFT"
    model = "gpt-3.5-turbo"
    weights = '{"technical_analysis": 0.40, "company_news": 0.30, "world_news": 0.15, "industry_changes": 0.15}'
    analysis_type = "week"
    test = "yes"
    
    print(f"Analysis Event Date: {analysis_event_date}")
    print(f"Company Ticker: {company_ticker}")
    print(f"Analysis Type: {analysis_type}")
    print(f"Weights: {weights}")
    print("-" * 60)
    
    # Run the analysis
    result = self_ai_analysis_by_ticker(
        analysis_event_date=analysis_event_date,
        company_ticker=company_ticker,
        model=model,
        weights=weights,
        analysis_type=analysis_type,
        test=test
    )
    
    # Display results
    print("\nResults:")
    print("-" * 30)
    if result['success']:
        print(f"✅ Week analysis completed successfully!")
        print(f"📊 Grade: {result['grade']}")
        print(f"📝 Text Analysis: {result['text_analysis']}")
        print(f"🤖 Model Used: {result['model']}")
        print(f"🔢 Tokens Used: {result['prompt_tokens'] + result['execution_tokens']}")
    else:
        print(f"❌ Week analysis failed: {result.get('error', 'Unknown error')}")
    
    return result


def test_error_handling():
    """
    Mission: Test error handling with invalid inputs.
    """
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    # Test with invalid analysis type
    try:
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="AAPL",
            model="gpt-3.5-turbo",
            weights='{"test": 0.5}',
            analysis_type="invalid_type",
            test="no"
        )
        print(f"❌ Should have failed with invalid analysis_type: {result}")
    except Exception as e:
        print(f"✅ Correctly caught error for invalid analysis_type: {e}")
    
    # Test with invalid weights JSON
    try:
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="AAPL",
            model="gpt-3.5-turbo",
            weights='invalid json',
            analysis_type="day",
            test="no"
        )
        print(f"✅ Handled invalid JSON gracefully: {result.get('success', False)}")
    except Exception as e:
        print(f"❌ Unexpected error with invalid JSON: {e}")
    
    # Test with empty ticker
    try:
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="",
            model="gpt-3.5-turbo",
            weights='{"test": 0.5}',
            analysis_type="day",
            test="no"
        )
        print(f"❌ Should have failed with empty ticker: {result}")
    except Exception as e:
        print(f"✅ Correctly caught error for empty ticker: {e}")


if __name__ == "__main__":
    # Run all tests
    print("Starting Self AI Analysis Tests...")
    
    # Test basic functionality
    basic_result = test_basic_functionality()
    
    # Test week analysis
    week_result = test_week_analysis()
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Basic Analysis: {'✅ PASS' if basic_result.get('success') else '❌ FAIL'}")
    print(f"Week Analysis: {'✅ PASS' if week_result.get('success') else '❌ FAIL'}")
    print("Error Handling: ✅ PASS (if no exceptions above)")
    
    print("\n🎉 All tests completed!") 
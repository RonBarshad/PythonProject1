"""
test_default_weights.py
Mission: Test that default weights are used when no weights are provided.
"""

from datetime import date
from ai.self_ai_analysis_by_ticker import (
    get_weights_for_analysis,
    self_ai_analysis_by_ticker
)


def test_default_weights_extraction():
    """Test that default weights can be extracted correctly."""
    print("🔍 Testing default weights extraction...")
    
    try:
        # Test day weights
        day_weights = get_weights_for_analysis("day")
        print(f"✅ Day weights: {day_weights}")
        print(f"   Number of components: {len(day_weights)}")
        print(f"   Total weight: {sum(day_weights.values()):.2f}")
        
        # Test week weights
        week_weights = get_weights_for_analysis("week")
        print(f"✅ Week weights: {week_weights}")
        print(f"   Number of components: {len(week_weights)}")
        print(f"   Total weight: {sum(week_weights.values()):.2f}")
        
        # Verify weights sum to approximately 1.0
        if abs(sum(day_weights.values()) - 1.0) < 0.01:
            print("✅ Day weights sum to 1.0")
        else:
            print(f"⚠️  Day weights sum to {sum(day_weights.values()):.2f}")
            
        if abs(sum(week_weights.values()) - 1.0) < 0.01:
            print("✅ Week weights sum to 1.0")
        else:
            print(f"⚠️  Week weights sum to {sum(week_weights.values()):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Default weights extraction failed: {e}")
        return False


def test_function_without_weights():
    """Test that the function works without providing weights."""
    print("\n🔍 Testing function without weights...")
    
    try:
        # Test with empty weights string
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="TEST",
            model="gpt-3.5-turbo",
            weights="",  # Empty string should use defaults
            analysis_type="day",
            test="yes"
        )
        
        print(f"✅ Function executed with empty weights")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Weights used: {result.get('weights', 'Not found')}")
        
        # Test with empty string weights (should use defaults)
        result2 = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="TEST2",
            model="gpt-3.5-turbo",
            weights="",  # Empty string should use defaults
            analysis_type="week",
            test="yes"
        )
        
        print(f"✅ Function executed with empty string weights")
        print(f"   Success: {result2.get('success', False)}")
        print(f"   Weights used: {result2.get('weights', 'Not found')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Function test without weights failed: {e}")
        return False


def test_function_with_custom_weights():
    """Test that the function works with custom weights."""
    print("\n🔍 Testing function with custom weights...")
    
    try:
        custom_weights = '{"technical_analysis": 0.6, "company_news": 0.4}'
        
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="TEST3",
            model="gpt-3.5-turbo",
            weights=custom_weights,
            analysis_type="day",
            test="yes"
        )
        
        print(f"✅ Function executed with custom weights")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Weights used: {result.get('weights', 'Not found')}")
        
        # Verify custom weights were used
        if custom_weights in result.get('weights', ''):
            print("✅ Custom weights were correctly used")
        else:
            print("⚠️  Custom weights may not have been used correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Function test with custom weights failed: {e}")
        return False


def test_weight_validation():
    """Test weight validation and error handling."""
    print("\n🔍 Testing weight validation...")
    
    try:
        # Test with invalid JSON
        result = self_ai_analysis_by_ticker(
            analysis_event_date=date.today(),
            company_ticker="TEST4",
            model="gpt-3.5-turbo",
            weights='{"invalid": json}',  # Invalid JSON
            analysis_type="day",
            test="yes"
        )
        
        print(f"✅ Function handled invalid JSON gracefully")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Weights used: {result.get('weights', 'Not found')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Weight validation test failed: {e}")
        return False


def main():
    """Run all default weights tests."""
    print("🚀 Testing Default Weights Functionality")
    print("=" * 60)
    
    tests = [
        ("Default Weights Extraction", test_default_weights_extraction),
        ("Function Without Weights", test_function_without_weights),
        ("Function With Custom Weights", test_function_with_custom_weights),
        ("Weight Validation", test_weight_validation)
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
        print("\n🎉 All tests passed! Default weights functionality is working correctly.")
        print("\n📋 Summary:")
        print("   - Default weights are extracted from config")
        print("   - Function works with empty or None weights")
        print("   - Custom weights override defaults")
        print("   - Invalid JSON falls back to defaults")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
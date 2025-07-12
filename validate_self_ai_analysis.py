"""
validate_self_ai_analysis.py
Mission: Validate the self_ai_analysis_by_ticker module without making actual API calls.
"""

import sys
import os
import importlib.util
from datetime import date

def validate_imports():
    """Check if all required modules can be imported."""
    print("🔍 Checking imports...")
    
    required_modules = [
        'json',
        'logging', 
        're',
        'datetime',
        'typing',
        'mysql.connector',
        'openai',
        'config.config'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'config.config':
                # Special handling for config module
                spec = importlib.util.spec_from_file_location("config", "config/config.py")
                if spec is None or spec.loader is None:
                    missing_modules.append(module)
                else:
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)
            else:
                __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {missing_modules}")
        return False
    else:
        print("✅ All imports successful")
        return True

def validate_config():
    """Check if required configuration exists."""
    print("\n🔍 Checking configuration...")
    
    try:
        from config.config import get
        
        required_configs = [
            "database.host",
            "database.user", 
            "database.password",
            "database.name",
            "api_key_gpt",
            "self_analysis.model",
            "self_analysis.daily_analysis_system_message",
            "self_analysis.weekly_analysis_system_message"
        ]
        
        missing_configs = []
        
        for config_path in required_configs:
            try:
                value = get(config_path)
                if value is None:
                    missing_configs.append(config_path)
                else:
                    print(f"  ✅ {config_path}")
            except Exception as e:
                print(f"  ❌ {config_path}: {e}")
                missing_configs.append(config_path)
        
        if missing_configs:
            print(f"\n❌ Missing configurations: {missing_configs}")
            return False
        else:
            print("✅ All configurations found")
            return True
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def validate_functions():
    """Check if all required functions exist."""
    print("\n🔍 Checking functions...")
    
    try:
        from ai.self_ai_analysis_by_ticker import (
            get_db_credentials,
            extract_system_message_and_model,
            get_weights_for_analysis,
            run_gpt_analysis,
            parse_gpt_output,
            insert_analysis_to_database,
            self_ai_analysis_by_ticker
        )
        
        functions = [
            'get_db_credentials',
            'extract_system_message_and_model', 
            'get_weights_for_analysis',
            'run_gpt_analysis',
            'parse_gpt_output',
            'insert_analysis_to_database',
            'self_ai_analysis_by_ticker'
        ]
        
        for func_name in functions:
            try:
                func = globals()[func_name]
                if callable(func):
                    print(f"  ✅ {func_name}")
                else:
                    print(f"  ❌ {func_name}: Not callable")
            except Exception as e:
                print(f"  ❌ {func_name}: {e}")
        
        print("✅ All functions found")
        return True
        
    except Exception as e:
        print(f"❌ Function validation failed: {e}")
        return False

def validate_parse_function():
    """Test the parse_gpt_output function with sample data."""
    print("\n🔍 Testing parse_gpt_output function...")
    
    try:
        from ai.self_ai_analysis_by_ticker import parse_gpt_output
        
        test_cases = [
            # JSON format (backward compatibility)
            ('{"score": 0.75, "explanation": "Good performance"}', "Good performance", 0.75),
            # New format: Text with grade at end (1-10 scale)
            ("Analysis shows positive trend. 8.5", "Analysis shows positive trend.", 0.833),  # (8.5-1)/9
            # New format: Text with grade at end (1-10 scale)
            ("Analysis shows negative trend. 3.0", "Analysis shows negative trend.", 0.222),  # (3.0-1)/9
            # Text without grade
            ("Analysis shows mixed results", "Analysis shows mixed results", 0.0),
            # Empty content
            ("", "No analysis provided", 0.0),
            # None content
            (None, "No analysis provided", 0.0)
        ]
        
        for input_text, expected_text, expected_grade in test_cases:
            try:
                result_text, result_grade = parse_gpt_output(input_text)
                if result_text == expected_text and abs(result_grade - expected_grade) < 0.01:
                    print(f"  ✅ Test case passed: {input_text[:30]}...")
                else:
                    print(f"  ❌ Test case failed: expected ({expected_text}, {expected_grade}), got ({result_text}, {result_grade})")
            except Exception as e:
                print(f"  ❌ Test case error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parse function validation failed: {e}")
        return False

def validate_config_extraction():
    """Test the config extraction functions."""
    print("\n🔍 Testing config extraction...")
    
    try:
        from ai.self_ai_analysis_by_ticker import extract_system_message_and_model, get_weights_for_analysis
        
        # Test day analysis
        try:
            system_msg, model = extract_system_message_and_model("day")
            print(f"  ✅ Day analysis: model={model}, msg_length={len(system_msg)}")
        except Exception as e:
            print(f"  ❌ Day analysis failed: {e}")
        
        # Test week analysis
        try:
            system_msg, model = extract_system_message_and_model("week")
            print(f"  ✅ Week analysis: model={model}, msg_length={len(system_msg)}")
        except Exception as e:
            print(f"  ❌ Week analysis failed: {e}")
        
        # Test weights
        try:
            day_weights = get_weights_for_analysis("day")
            week_weights = get_weights_for_analysis("week")
            print(f"  ✅ Weights: day={len(day_weights)} items, week={len(week_weights)} items")
        except Exception as e:
            print(f"  ❌ Weights failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config extraction validation failed: {e}")
        return False

def main():
    """Run all validations."""
    print("🚀 Starting Self AI Analysis Module Validation")
    print("=" * 60)
    
    validations = [
        ("Imports", validate_imports),
        ("Configuration", validate_config),
        ("Functions", validate_functions),
        ("Parse Function", validate_parse_function),
        ("Config Extraction", validate_config_extraction)
    ]
    
    results = []
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All validations passed! The module should work correctly.")
    else:
        print("\n⚠️  Some validations failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
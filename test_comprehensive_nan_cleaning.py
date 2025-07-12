#!/usr/bin/env python3
"""
Comprehensive test script to verify NaN cleaning functionality.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import clean_dataframe_for_mysql, safe_mysql_insert
from config.config import get

def test_comprehensive_nan_cleaning():
    """Test that all types of NaN values are properly cleaned."""
    
    # Create a test DataFrame with various types of NaN values
    test_data = {
        'event_date': ['2025-06-29 21:30:00'],
        'insertion_time': ['2025-06-29 21:30:00'],
        'company_ticker': ['TEST'],
        'analysis_type': ['comprehensive_test'],
        'weight': [float('nan')],  # numpy nan
        'grade': [np.nan],         # numpy nan
        'text_analysis': ['Test with various NaN types'],
        'AI_model': ['gpt-3.5-turbo'],
        'prompt_tokens': ['nan'],   # string nan
        'execution_tokens': ['NaN'] # string NaN
    }
    
    df = pd.DataFrame(test_data)
    
    print("=" * 60)
    print("COMPREHENSIVE NaN CLEANING TEST")
    print("=" * 60)
    
    print("\nOriginal DataFrame:")
    print(df)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"DataFrame dtypes: {df.dtypes}")
    
    # Check for NaN values in original DataFrame
    print("\nNaN values in original DataFrame:")
    for col in df.columns:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            print(f"  {col}: {nan_count} NaN values")
    
    # Clean the DataFrame
    print("\n" + "=" * 40)
    print("CLEANING DATAFRAME...")
    print("=" * 40)
    
    df_clean = clean_dataframe_for_mysql(df)
    
    print("\nCleaned DataFrame:")
    print(df_clean)
    
    # Check for NaN values in cleaned DataFrame
    print("\nNaN values in cleaned DataFrame:")
    for col in df_clean.columns:
        nan_count = df_clean[col].isna().sum()
        if nan_count > 0:
            print(f"  {col}: {nan_count} NaN values")
        else:
            print(f"  {col}: No NaN values ✅")
    
    # Check for None values in cleaned DataFrame
    print("\nNone values in cleaned DataFrame:")
    for col in df_clean.columns:
        none_count = (df_clean[col] == None).sum()
        if none_count > 0:
            print(f"  {col}: {none_count} None values")
    
    # Test safe MySQL insertion
    print("\n" + "=" * 40)
    print("TESTING SAFE MYSQL INSERTION...")
    print("=" * 40)
    
    try:
        table = get("database.other_tables.ai_analysis")
        col_map = get("ai_analysis.col_map")
        
        print(f"Target table: {table}")
        print(f"Column map: {col_map}")
        
        success = safe_mysql_insert(df_clean, table, col_map)
        
        if success:
            print("✅ Safe MySQL insertion completed successfully!")
        else:
            print("❌ Safe MySQL insertion failed!")
            
    except Exception as e:
        print(f"❌ Error during safe MySQL insertion: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_comprehensive_nan_cleaning() 
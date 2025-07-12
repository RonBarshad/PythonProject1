#!/usr/bin/env python3
"""
Test script to verify NaN handling in the ai_analysis table insertion.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import get
import database.connection as db_connection
import ai.analysis_runner as ai_runner

def test_nan_handling():
    """Test that NaN values are properly handled in ai_analysis table insertion."""
    
    # Create a test DataFrame with NaN values in multiple columns
    test_data = {
        'event_date': ['2025-06-29 21:00:00'],
        'insertion_time': ['2025-06-29 21:00:00'],
        'company_ticker': ['TEST'],
        'analysis_type': ['test_analysis'],
        'weight': [float('nan')],  # NaN in weight column
        'grade': [float('nan')],   # NaN in grade column
        'text_analysis': ['Test analysis with NaN values'],
        'AI_model': ['gpt-3.5-turbo'],
        'prompt_tokens': [float('nan')],  # NaN in prompt_tokens column
        'execution_tokens': [50]
    }
    
    df = pd.DataFrame(test_data)
    print("Original DataFrame:")
    print(df)
    print(f"Weight value: {df['weight'].iloc[0]}")
    print(f"Grade value: {df['grade'].iloc[0]}")
    print(f"Prompt tokens value: {df['prompt_tokens'].iloc[0]}")
    
    # Test the insert_data function
    try:
        table = get("database.other_tables.ai_analysis")
        col_map = get("ai_analysis.col_map")
        
        print(f"\nInserting into table: {table}")
        print(f"Using column map: {col_map}")
        
        # This should handle the NaN values properly in ALL columns
        db_connection.insert_data(df, table, col_map)
        print("✅ Insertion completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during insertion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nan_handling() 
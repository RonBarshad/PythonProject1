"""
utils/helpers.py
Mission: This module provides utility functions for data processing, validation, and common operations used across the stock analysis bot.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def validate_ticker(ticker: str) -> bool:
    """
    Mission: Validate if a ticker symbol is properly formatted.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        True if valid, False otherwise
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Basic validation: alphanumeric, 1-10 characters
    if not ticker.isalnum() or len(ticker) > 10:
        return False
    
    return True

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mission: Clean a DataFrame by removing duplicates, handling missing values, and standardizing data types.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    if df.empty:
        return df
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Handle missing values
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Convert date columns to datetime
    date_columns = df.select_dtypes(include=['object']).columns
    for col in date_columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    
    return df

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Mission: Safely convert a value to float with error handling.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Mission: Format a decimal value as a percentage string.
    
    Args:
        value: Decimal value (0.0 to 1.0)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    try:
        percentage = value * 100
        return f"{percentage:.{decimal_places}f}%"
    except:
        return "0.00%"

def validate_config_required_keys(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Mission: Validate that a configuration dictionary contains all required keys.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required keys
        
    Returns:
        True if all keys are present, False otherwise
    """
    missing_keys = []
    for key in required_keys:
        if key not in config or config[key] is None:
            missing_keys.append(key)
    
    if missing_keys:
        logging.error(f"Missing required configuration keys: {missing_keys}")
        return False
    
    return True

def clean_dataframe_for_mysql(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mission: Comprehensive cleaning of DataFrame to ensure no NaN-like values make it to MySQL.
    This function handles all possible types of NaN values that could cause database insertion issues.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The DataFrame to clean
        
    Returns:
    --------
    pd.DataFrame
        Cleaned DataFrame with all NaN-like values replaced with None
    """
    if df.empty:
        return df
    
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Step 1: Replace all known NaN types with None
    nan_replacements = [
        np.nan, 
        float('nan'), 
        'nan', 
        'NaN', 
        'NAN', 
        'null', 
        'NULL', 
        'Null',
        'None',
        'none',
        'NONE'
    ]
    
    df_clean = df_clean.replace(nan_replacements, None)
    
    # Step 2: Use pandas built-in method to catch any remaining NaN values
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    # Step 3: Final comprehensive check for each cell
    for col in df_clean.columns:
        for idx in df_clean.index:
            value = df_clean.at[idx, col]
            if pd.isna(value) or (isinstance(value, str) and value.lower() in ['nan', 'null', 'none']):
                df_clean.at[idx, col] = None
    
    logging.info(f"DataFrame cleaned: {df_clean.shape[0]} rows, {df_clean.shape[1]} columns")
    return df_clean

def safe_mysql_insert(df: pd.DataFrame, table: str, col_map: dict = {}) -> bool:
    """
    Mission: Safely insert DataFrame into MySQL with comprehensive NaN cleaning.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to insert
    table : str
        Target table name
    col_map : dict, optional
        Column mapping dictionary
        
    Returns:
    --------
    bool
        True if insertion was successful, False otherwise
    """
    try:
        # Clean the DataFrame first
        df_clean = clean_dataframe_for_mysql(df)
        
        # Import here to avoid circular imports
        import database.connection as db_connection
        
        # Use the existing insert_data function with cleaned DataFrame
        if col_map is not None:
            db_connection.insert_data(df_clean, table, col_map)
        else:
            db_connection.insert_data(df_clean, table)
        
        logging.info(f"✅ Successfully inserted {len(df_clean)} rows into {table}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to insert data into {table}: {e}")
        return False 
"""
Data Validation Utilities
Validates user data and event data before database operations
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it has 7-15 digits (international standard)
    return 7 <= len(digits_only) <= 15

def validate_ticker(ticker: str) -> bool:
    """
    Validate stock ticker format
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not ticker:
        return False
    
    # Ticker should be 1-10 characters, alphanumeric
    pattern = r'^[A-Za-z0-9]{1,10}$'
    return bool(re.match(pattern, ticker))

def validate_user_data(user_data: Dict[str, Any], is_update: bool = False) -> bool:
    """
    Validate user data for database operations
    
    Args:
        user_data: User data dictionary
        is_update: True if this is an update operation
        
    Returns:
        True if valid, False otherwise
    """
    if not user_data or not isinstance(user_data, dict):
        return False
    
    # Required fields for creation
    if not is_update:
        required_fields = ['user_id']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                return False
    
    # Validate email if present
    if 'email' in user_data and user_data['email']:
        if not validate_email(user_data['email']):
            return False
    
    # Validate phone number if present
    if 'phone_number' in user_data and user_data['phone_number']:
        if not validate_phone_number(user_data['phone_number']):
            return False
    
    # Validate telegram_user_id if present
    if 'telegram_user_id' in user_data and user_data['telegram_user_id']:
        if not isinstance(user_data['telegram_user_id'], str):
            return False
    
    # Validate plan_type if present
    if 'plan_type' in user_data and user_data['plan_type']:
        valid_plans = ['free', 'basic', 'premium', 'pro']
        if user_data['plan_type'] not in valid_plans:
            return False
    
    # Validate numeric fields
    numeric_fields = ['amount_tickers_allowed', 'amount_tickers_have']
    for field in numeric_fields:
        if field in user_data and user_data[field] is not None:
            if not isinstance(user_data[field], int) or user_data[field] < 0:
                return False
    
    # Validate status if present
    if 'status' in user_data and user_data['status']:
        valid_statuses = ['active', 'inactive', 'suspended']
        if user_data['status'] not in valid_statuses:
            return False
    
    return True

def validate_event_data(event_data: Dict[str, Any]) -> bool:
    """
    Validate event data for logging
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    if not event_data or not isinstance(event_data, dict):
        return False
    
    # Required fields
    required_fields = ['user_id', 'event_type']
    for field in required_fields:
        if field not in event_data or not event_data[field]:
            return False
    
    # Validate event_type
    valid_event_types = [
        'first_connection',
        'sign_in_granted',
        'sign_up_granted',
        'cooldown_attempts',
        'daily_message_sent',
        'menu_sent',
        'function_write_call',
        'stock_analysis_pushed',
        'details_changed',
        'purchase_start',
        'purchase_shown',
        'product_choose',
        'message_received'
    ]
    
    if event_data['event_type'] not in valid_event_types:
        return False
    
    # Validate telegram_id if present
    if 'telegram_id' in event_data and event_data['telegram_id']:
        if not isinstance(event_data['telegram_id'], str):
            return False
    
    # Validate email if present
    if 'user_email' in event_data and event_data['user_email']:
        if not validate_email(event_data['user_email']):
            return False
    
    # Validate user_plan if present
    if 'user_plan' in event_data and event_data['user_plan']:
        valid_plans = ['free', 'basic', 'premium', 'pro']
        if event_data['user_plan'] not in valid_plans:
            return False
    
    # Validate text fields length
    text_fields = ['before_change', 'after_change', 'product_purchase']
    for field in text_fields:
        if field in event_data and event_data[field]:
            if not isinstance(event_data[field], str) or len(event_data[field]) > 1000:
                return False
    
    return True

def validate_ticker_list(tickers: str) -> bool:
    """
    Validate comma-separated ticker list
    
    Args:
        tickers: Comma-separated ticker string
        
    Returns:
        True if valid, False otherwise
    """
    if not tickers:
        return True  # Empty list is valid
    
    ticker_list = [ticker.strip() for ticker in tickers.split(',')]
    
    for ticker in ticker_list:
        if ticker and not validate_ticker(ticker):
            return False
    
    return True

def validate_weights(weights: str) -> bool:
    """
    Validate portfolio weights string
    
    Args:
        weights: Comma-separated weights string
        
    Returns:
        True if valid, False otherwise
    """
    if not weights:
        return True  # Empty weights is valid
    
    try:
        weight_list = [float(w.strip()) for w in weights.split(',')]
        
        # Check if weights sum to approximately 100%
        total_weight = sum(weight_list)
        if abs(total_weight - 100.0) > 0.1:  # Allow small rounding errors
            return False
        
        # Check if all weights are positive
        for weight in weight_list:
            if weight < 0:
                return False
        
        return True
    except (ValueError, TypeError):
        return False

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
    sanitized = text
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()

def validate_coupon_code(coupon: str) -> bool:
    """
    Validate coupon code format
    
    Args:
        coupon: Coupon code string
        
    Returns:
        True if valid, False otherwise
    """
    if not coupon:
        return False
    
    # Coupon should be 3-20 characters, alphanumeric and hyphens
    pattern = r'^[A-Za-z0-9\-]{3,20}$'
    return bool(re.match(pattern, coupon))

def validate_product_id(product_id: str) -> bool:
    """
    Validate product ID format
    
    Args:
        product_id: Product ID string
        
    Returns:
        True if valid, False otherwise
    """
    if not product_id:
        return False
    
    # Product ID should be 1-50 characters, alphanumeric and hyphens
    pattern = r'^[A-Za-z0-9\-]{1,50}$'
    return bool(re.match(pattern, product_id)) 
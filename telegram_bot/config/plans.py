"""
Subscription Plans Configuration
Defines all available plans and their features
"""

from typing import Dict, List, Any

# Available subscription plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0.00,
        'max_tickers': 3,
        'features': [
            'basic_analysis',
            'daily_summary',
            'basic_charts'
        ],
        'description': 'Basic stock analysis with limited tickers',
        'duration_days': 30
    },
    
    'basic': {
        'name': 'Basic Plan',
        'price': 4.99,
        'max_tickers': 5,
        'features': [
            'basic_analysis',
            'daily_summary',
            'basic_charts',
            'technical_indicators',
            'email_alerts'
        ],
        'description': 'Enhanced analysis with more tickers and indicators',
        'duration_days': 30
    },
    
    'premium': {
        'name': 'Premium Plan',
        'price': 9.99,
        'max_tickers': 10,
        'features': [
            'basic_analysis',
            'daily_summary',
            'basic_charts',
            'technical_indicators',
            'email_alerts',
            'advanced_indicators',
            'portfolio_weights',
            'custom_alerts',
            'priority_support'
        ],
        'description': 'Full-featured analysis with portfolio management',
        'duration_days': 30
    },
    
    'pro': {
        'name': 'Pro Plan',
        'price': 19.99,
        'max_tickers': 20,
        'features': [
            'basic_analysis',
            'daily_summary',
            'basic_charts',
            'technical_indicators',
            'email_alerts',
            'advanced_indicators',
            'portfolio_weights',
            'custom_alerts',
            'priority_support',
            'ai_insights',
            'backtesting',
            'api_access'
        ],
        'description': 'Professional tools with AI insights and backtesting',
        'duration_days': 30
    }
}

# Feature descriptions for UI
FEATURE_DESCRIPTIONS = {
    'basic_analysis': 'Basic stock price analysis and trends',
    'daily_summary': 'Daily market summary and portfolio updates',
    'basic_charts': 'Price charts and volume analysis',
    'technical_indicators': 'RSI, MACD, Moving Averages',
    'email_alerts': 'Email notifications for price movements',
    'advanced_indicators': 'Bollinger Bands, Stochastic, Williams %R',
    'portfolio_weights': 'Customize portfolio allocation weights',
    'custom_alerts': 'Set custom price and volume alerts',
    'priority_support': 'Priority customer support',
    'ai_insights': 'AI-powered market insights and predictions',
    'backtesting': 'Test strategies on historical data',
    'api_access': 'API access for custom integrations'
}

# Plan comparison for UI
PLAN_COMPARISON = {
    'free': {
        'tickers': 3,
        'price': '$0',
        'features': ['Basic Analysis', 'Daily Summary', 'Basic Charts'],
        'recommended': False
    },
    'basic': {
        'tickers': 5,
        'price': '$4.99',
        'features': ['Basic Analysis', 'Daily Summary', 'Basic Charts', 'Technical Indicators', 'Email Alerts'],
        'recommended': False
    },
    'premium': {
        'tickers': 10,
        'price': '$9.99',
        'features': ['All Basic Features', 'Advanced Indicators', 'Portfolio Weights', 'Custom Alerts', 'Priority Support'],
        'recommended': True
    },
    'pro': {
        'tickers': 20,
        'price': '$19.99',
        'features': ['All Premium Features', 'AI Insights', 'Backtesting', 'API Access'],
        'recommended': False
    }
}

def get_plan_features(plan_name: str) -> List[str]:
    """
    Get features for a specific plan
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        List of feature names
    """
    if plan_name in SUBSCRIPTION_PLANS:
        return SUBSCRIPTION_PLANS[plan_name]['features']
    return []

def has_feature(plan_name: str, feature: str) -> bool:
    """
    Check if a plan has a specific feature
    
    Args:
        plan_name: Name of the plan
        feature: Feature to check
        
    Returns:
        True if plan has the feature, False otherwise
    """
    features = get_plan_features(plan_name)
    return feature in features

def get_plan_by_name(plan_name: str) -> Dict[str, Any]:
    """
    Get complete plan information by name
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        Plan configuration dictionary
    """
    return SUBSCRIPTION_PLANS.get(plan_name, {})

def get_all_plans() -> Dict[str, Dict[str, Any]]:
    """
    Get all available plans
    
    Returns:
        Dictionary of all plans
    """
    return SUBSCRIPTION_PLANS

def get_plan_price(plan_name: str) -> float:
    """
    Get price for a specific plan
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        Plan price
    """
    plan = get_plan_by_name(plan_name)
    return plan.get('price', 0.0)

def get_max_tickers(plan_name: str) -> int:
    """
    Get maximum tickers allowed for a plan
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        Maximum number of tickers
    """
    plan = get_plan_by_name(plan_name)
    return plan.get('max_tickers', 3) 
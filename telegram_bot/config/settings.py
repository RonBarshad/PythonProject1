"""
Bot Settings Configuration
Contains all configurable settings for the Telegram bot
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from telegram_bot.config.config import get


# Bot Configuration
BOT_TOKEN = get("telegram.bot_token")

# Telegram Configuration
TELEGRAM_CONFIG = {
    'telegram_bot_public_key': get("telegram.telegram_bot_public_key"),
    'app_id': get("telegram.app_id"),
    'api_hash': get("telegram.api_hash"),
    'app_shortname': get("telegram.app_shortname"),
    'app_title': get("telegram.app_title"),
    'user_id': int(get("telegram.user_id")),
    'bot_name': get("telegram.bot_name"),
    'bot_username': get("telegram.bot_username")
}

# OpenAI Configuration
OPENAI_CONFIG = {
    'api_key': get("api_key_gpt"),
    'model': get("technical_analysis.model"),
    'temperature': get("technical_analysis.temperature"),
    'max_tokens': get("technical_analysis.max_tokens")
}

# OpenAI individual variables for backward compatibility
OPENAI_API_KEY = get("api_key_gpt")
OPENAI_MODEL = get("technical_analysis.model")
OPENAI_TEMPERATURE = get("technical_analysis.temperature")
OPENAI_MAX_TOKENS = get("technical_analysis.max_tokens")
OPENAI_TOP_P = 1.0  # Default value
OPENAI_FREQUENCY_PENALTY = 0.0  # Default value
OPENAI_PRESENCE_PENALTY = 0.0  # Default value
OPENAI_STOP_SEQUENCE = None  # Default value

# API Keys Configuration
API_KEYS = {
    'api_key_gpt': get("api_key_gpt"),
    'api_key_finnhub': get("api_key_finnhub"),
    'api_key_alpha_vantage': get("api_key_alpha_vantage")
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': get("smtp_server"),
    'smtp_port': int(get("smtp_port")),
    'smtp_user': get("smtp_user"),
    'smtp_password': get("smtp_password")
}

# Database Configuration
DATABASE_CONFIG = {
    'host': get("database.host"),
    'port': int(get("database.port")),
    'user': get("database.user"),
    'password': get("database.password"),
    'database': get("database.name"),
    'charset': 'utf8mb4'
}

# Bot Settings
BOT_SETTINGS = {
    'max_retry_attempts': 15,
    'cooldown_minutes': 30,
    'session_timeout_minutes': 60,
    'max_tickers_free': 3,
    'max_tickers_premium': 10,
    'default_language': 'en'
}

# Rate Limiting
RATE_LIMITS = {
    'messages_per_minute': 10,
    'analysis_requests_per_hour': 50,
    'settings_changes_per_hour': 20
}

# Feature Flags
FEATURES = {
    'weights_enabled': True,
    'advanced_analysis': True,
    'payment_processing': True,
    'daily_messages': True
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bot.log'
}

# Development Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true' 
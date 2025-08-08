import json
import os
from pathlib import Path
from functools import lru_cache
from typing import Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

_CONFIG_PATH = Path(__file__).parent / "config.json"

@lru_cache
def _raw_cfg() -> dict[str, Any]:
    """Read & cache config.json once per process."""
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Override with environment variables if they exist
    env_overrides = {
        "api_key_gpt": os.getenv("OPENAI_API_KEY"),
        "api_key_finnhub": os.getenv("FINNHUB_API_KEY"),
        "api_key_alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "smtp_server": os.getenv("SMTP_SERVER"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_password": os.getenv("SMTP_PASSWORD"),
    }
    
    # Apply environment variable overrides
    for key, value in env_overrides.items():
        if value is not None:
            config[key] = value
    
    # Override database config if environment variables exist
    db_port = os.getenv("DB_PORT")
    if db_port:
        config["database"]["port"] = int(db_port)
    
    db_host = os.getenv("DB_HOST")
    if db_host:
        config["database"]["host"] = db_host
    
    db_user = os.getenv("DB_USER")
    if db_user:
        config["database"]["user"] = db_user
    
    db_password = os.getenv("DB_PASSWORD")
    if db_password:
        config["database"]["password"] = db_password
    
    db_name = os.getenv("DB_NAME")
    if db_name:
        config["database"]["name"] = db_name
    
    # Override telegram config if environment variables exist
    telegram_app_id = os.getenv("TELEGRAM_APP_ID")
    if telegram_app_id:
        config["telegram"]["app_id"] = telegram_app_id
    
    telegram_api_hash = os.getenv("TELEGRAM_API_HASH")
    if telegram_api_hash:
        config["telegram"]["api_hash"] = telegram_api_hash
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_bot_token:
        config["telegram"]["bot_token"] = telegram_bot_token
    
    telegram_bot_name = os.getenv("TELEGRAM_BOT_NAME")
    if telegram_bot_name:
        config["telegram"]["bot_name"] = telegram_bot_name
    
    telegram_bot_username = os.getenv("TELEGRAM_BOT_USERNAME")
    if telegram_bot_username:
        config["telegram"]["bot_username"] = telegram_bot_username
    
    telegram_bot_token_2 = os.getenv("TELEGRAM_BOT_TOKEN_2")
    if telegram_bot_token_2:
        config["telegram"]["bot_token_2"] = telegram_bot_token_2
    
    return config

def get(path: str, default: Any = None) -> Any:
    """
    Retrieve a value using dotted paths, e.g.:
        get("technical_analysis.model")  -> "gpt-4o-mini"
    """
    node = _raw_cfg()
    for part in path.split("."):
        if not isinstance(node, dict):
            return default
        node = node.get(part, default)
    return node


def print_system_message(topic: str) -> None:
    """
    Print the system message for the given topic (e.g., 'technical_analysis', 'analysts_rating', 'news_analysis').
    """
    topic_map = {
        'technical_analysis': 'technical_analysis.system_message',
        'analysts_rating': 'analyst_opinion.system_message',
        'news_analysis': 'news_analysis.system_message',
    }
    path = topic_map.get(topic)
    if not path:
        print(f"Unknown topic: {topic}")
        return
    msg = get(path)
    print(f"System message for {topic}:\n{msg}")


def set_system_message(topic: str, new_message: str) -> None:
    """
    Update the system message for the given topic.
    """
    topic_map = {
        'technical_analysis': 'technical_analysis.system_message',
        'analysts_rating': 'analyst_opinion.system_message',
        'news_analysis': 'news_analysis.system_message',
    }
    path = topic_map.get(topic)
    if not path:
        print(f"Unknown topic: {topic}")
        return
    
    # Read current config
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Update the message
    path_parts = path.split(".")
    current = config
    for part in path_parts[:-1]:
        current = current[part]
    current[path_parts[-1]] = new_message
    
    # Write back to file
    with _CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Updated system message for {topic}") 
import json
from pathlib import Path
from functools import lru_cache
from typing import Any

_CONFIG_PATH = Path(__file__).parent / "config.json"

@lru_cache
def _raw_cfg() -> dict[str, Any]:
    """Read & cache config.json once per process."""
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

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
import json
import os
from pathlib import Path


# Load configuration from config.json
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()

RSS_URL = CONFIG["news"]["sources"]["rss"]["url"]
API_URL = CONFIG["news"]["sources"]["api"]["url"]
CRAWLER_URL = CONFIG["news"]["sources"]["crawler"]["url"]
LANGUAGE = CONFIG["news"]["language"]

# AI model configuration
GEMINI_MODEL = CONFIG["ai"]["model"]

# API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def validate_gemini_key():
    """Validate that GEMINI_API_KEY is present and return it, or raise EnvironmentError."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it before running 'summarize' or 'analyze'."
        )
    return key


# fixed category list for news articles; can be used in argparse choices
CATEGORIES = [
    "arts",
    "business",
    "culture",
    "economy",
    "education",
    "entertainment",
    "environment",
    "health",
    "politics",
    "science",
    "society",
    "sports",
    "technology",
    "travel",
]

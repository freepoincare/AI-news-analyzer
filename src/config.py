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


# API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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

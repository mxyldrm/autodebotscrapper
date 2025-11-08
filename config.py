"""
Configuration file for AutoDE Bot
Contains all settings and constants
"""

import os
from typing import Dict

# Bot Information
BOT_NAME = "AutoDE Bot"
BOT_VERSION = "2.0.0"

# Auto.de Scraping Configuration
BASE_URL = "https://www.auto.de/search?pageNumber={}&activeSort=NEWEST_OFFERS_FIRST"
RESPONSE_IDENTIFIER = "car-search-endpoint/api/v1/search/car/formatted"

# Scraping Parameters
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))  # Number of pages to scrape
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # Request timeout in seconds
VERIFY_SSL = True  # Always verify SSL certificates

# Rate Limiting (requests per time window)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # Time window in seconds

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # Initial delay in seconds
RETRY_BACKOFF = 2  # Backoff multiplier

# HTTP Headers (Updated User-Agent)
HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Telegram Configuration
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "autode_cars.db")
DELETE_OLD_CARS_DAYS = int(os.getenv("DELETE_OLD_CARS_DAYS", "7"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "autode_bot.log")

# Main Loop Configuration
MAIN_LOOP_INTERVAL = int(os.getenv("MAIN_LOOP_INTERVAL", "300"))  # 5 minutes default

# Safety Checks
CHECK_ROBOTS_TXT = os.getenv("CHECK_ROBOTS_TXT", "true").lower() == "true"

# Input Validation
MAX_STRING_LENGTH = 500
MAX_URL_LENGTH = 2000

def validate_config() -> bool:
    """
    Validates configuration settings
    Returns True if configuration is valid
    """
    errors = []

    # Check Telegram credentials
    if not TELEGRAM_API_KEY or TELEGRAM_API_KEY == "1":
        errors.append("TELEGRAM_API_KEY is not configured properly")

    if not CHAT_ID or CHAT_ID == "1":
        errors.append("TELEGRAM_CHAT_ID is not configured properly")

    # Check numeric values
    if MAX_PAGES < 1:
        errors.append("MAX_PAGES must be at least 1")

    if REQUEST_TIMEOUT < 5:
        errors.append("REQUEST_TIMEOUT must be at least 5 seconds")

    if errors:
        print("⚠️  Configuration warnings:")
        for error in errors:
            print(f"  - {error}")
        print("\nBot will continue but some features may not work properly.")
        print("Please check your .env file and configuration.\n")

    return len(errors) == 0

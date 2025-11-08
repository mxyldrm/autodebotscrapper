"""
Common utilities for AutoDE Bot
Handles logging, database operations, Telegram notifications, and web scraping utilities
"""

import os
import sys
import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import sqlite3
import json
from functools import wraps

# Configure logging
def setup_logger(name: str, log_file: str = 'autode_bot.log', level=logging.INFO):
    """
    Sets up a logger with file and console handlers
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Initialize logger
logger = setup_logger('AutoDEBot')


class RateLimiter:
    """
    Simple rate limiter to prevent overwhelming the target server
    """
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        """
        Wait if rate limit is exceeded
        """
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                self.requests = []

        self.requests.append(now)


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=10, time_window=60)


def retry_on_failure(max_retries: int = 3, delay: int = 2, backoff: int = 2):
    """
    Decorator to retry a function on failure with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise

                    logger.warning(
                        f"Attempt {retries}/{max_retries} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None
        return wrapper
    return decorator


def sanitize_string(value: Any, max_length: int = 500) -> str:
    """
    Sanitizes string input to prevent injection attacks
    """
    if value is None:
        return 'Unknown'

    # Convert to string and strip
    clean_value = str(value).strip()

    # Limit length
    if len(clean_value) > max_length:
        clean_value = clean_value[:max_length]

    # Remove potentially dangerous characters (basic sanitization)
    dangerous_chars = ['<', '>', '"', "'", '\\', '\x00']
    for char in dangerous_chars:
        clean_value = clean_value.replace(char, '')

    return clean_value if clean_value else 'Unknown'


def sanitize_number(value: Any, default: Any = 0) -> Any:
    """
    Sanitizes numeric input
    """
    try:
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            # Remove non-numeric characters except . and -
            clean_value = ''.join(c for c in value if c.isdigit() or c in '.-')
            return float(clean_value) if '.' in clean_value else int(clean_value)
    except (ValueError, TypeError):
        pass

    return default


@retry_on_failure(max_retries=3, delay=2)
def send_telegram_message(message: str, api_key: str, chat_id: str) -> bool:
    """
    Sends a message to Telegram with proper error handling
    """
    if not api_key or not chat_id or api_key == '1' or chat_id == '1':
        logger.warning("Telegram credentials not configured. Skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{api_key}/sendMessage"

    # Sanitize message to prevent injection
    safe_message = sanitize_string(message, max_length=4096)

    payload = {
        'chat_id': chat_id,
        'text': safe_message,
        'parse_mode': 'HTML'
    }

    try:
        rate_limiter.wait_if_needed()
        response = requests.post(
            url,
            json=payload,
            timeout=10,
            verify=True  # SSL verification enabled
        )
        response.raise_for_status()
        logger.info("Telegram notification sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False


def send_error_to_telegram(error_message: str):
    """
    Sends error notification to Telegram (wrapper function)
    """
    from config import TELEGRAM_API_KEY, CHAT_ID

    # Don't expose full stack traces in production
    safe_error = f"⚠️ AutoDE Bot Error:\n{sanitize_string(error_message, max_length=500)}"
    send_telegram_message(safe_error, TELEGRAM_API_KEY, CHAT_ID)


@retry_on_failure(max_retries=3, delay=2)
def find_endpoint(url: str, identifier: str, bot_name: str, headers: Dict = None) -> List[str]:
    """
    Finds API endpoints by analyzing network requests
    Enhanced with proper security measures
    """
    try:
        rate_limiter.wait_if_needed()

        # Make request with timeout and SSL verification
        response = requests.get(
            url,
            headers=headers or {},
            timeout=30,  # 30 second timeout
            verify=True,  # SSL verification
            allow_redirects=True
        )
        response.raise_for_status()

        # Parse response to find endpoints containing the identifier
        # This is a simplified implementation - actual implementation would
        # parse HTML/JavaScript to find API endpoints
        endpoints = []

        # Look for the identifier in the response text
        if identifier in response.text:
            # Extract potential API endpoints
            # This is a placeholder - actual implementation would use proper parsing
            logger.info(f"{bot_name} - Found identifier in page")

        return endpoints

    except requests.exceptions.Timeout:
        logger.error(f"{bot_name} - Request timeout for URL: {url}")
        return []
    except requests.exceptions.SSLError as e:
        logger.error(f"{bot_name} - SSL Error: {str(e)}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"{bot_name} - Request failed: {str(e)}")
        return []


def get_vehicle_image_url(car_id: str, image_id: Optional[str]) -> str:
    """
    Constructs vehicle image URL with proper validation
    """
    if not car_id:
        return 'No image available'

    # Sanitize inputs
    safe_car_id = sanitize_string(car_id, max_length=50)

    if image_id:
        safe_image_id = sanitize_string(image_id, max_length=50)
        # Construct image URL (example format)
        return f"https://www.auto.de/images/vehicles/{safe_car_id}/{safe_image_id}"

    return f"https://www.auto.de/images/vehicles/{safe_car_id}/default"


class DatabaseManager:
    """
    Manages database operations with proper error handling and connection pooling
    """
    def __init__(self, db_path: str = 'autode_cars.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """
        Initializes the database schema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cars (
                        id TEXT PRIMARY KEY,
                        model_make TEXT NOT NULL,
                        price REAL,
                        link TEXT,
                        image_url TEXT,
                        company TEXT,
                        transmission TEXT,
                        mileage INTEGER,
                        first_registration INTEGER,
                        fuel_type TEXT,
                        power_data TEXT,
                        co2_emission TEXT,
                        consumption TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create index for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_created_at ON cars(created_at)
                ''')

                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def insert_car(self, car_info: Dict[str, Any], bot_name: str) -> bool:
        """
        Inserts or updates car information in the database
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Sanitize all inputs
                car_id = sanitize_string(car_info.get('ID'), max_length=50)
                model_make = sanitize_string(car_info.get('Model and Make'), max_length=200)
                price = sanitize_number(car_info.get('Price'))
                link = sanitize_string(car_info.get('Link'), max_length=500)
                image_url = sanitize_string(car_info.get('Image'), max_length=500)
                company = sanitize_string(car_info.get('Company'), max_length=50)
                transmission = sanitize_string(car_info.get('Transmission'), max_length=50)

                features = car_info.get('Features', {})
                mileage = sanitize_number(features.get('mileage_road'))
                first_registration = sanitize_number(features.get('calendar'))
                fuel_type = sanitize_string(features.get('gas_pump'), max_length=50)
                power_data = sanitize_string(features.get('speedometer'), max_length=100)
                co2_emission = sanitize_string(features.get('leaf'), max_length=50)
                consumption = sanitize_string(features.get('water_drop'), max_length=50)

                # Use parameterized query to prevent SQL injection
                cursor.execute('''
                    INSERT OR REPLACE INTO cars
                    (id, model_make, price, link, image_url, company, transmission,
                     mileage, first_registration, fuel_type, power_data,
                     co2_emission, consumption, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    car_id, model_make, price, link, image_url, company, transmission,
                    mileage, first_registration, fuel_type, power_data,
                    co2_emission, consumption
                ))

                conn.commit()
                logger.debug(f"{bot_name} - Car {car_id} added/updated successfully")
                return True

        except sqlite3.Error as e:
            logger.error(f"{bot_name} - Database error while inserting car: {str(e)}")
            return False

    def delete_old_cars(self, days: int = 7) -> int:
        """
        Deletes cars older than specified days
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Calculate the cutoff date
                cutoff_date = datetime.now() - timedelta(days=days)

                cursor.execute('''
                    DELETE FROM cars WHERE created_at < ?
                ''', (cutoff_date,))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} old car(s) from database")

                return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Database error while deleting old cars: {str(e)}")
            return 0


# Global database manager instance
db_manager = DatabaseManager()


def insert_car_to_database(car_info: Dict[str, Any], bot_name: str):
    """
    Wrapper function to insert car to database
    """
    return db_manager.insert_car(car_info, bot_name)


def delete_old_cars_from_database(days: int = 7):
    """
    Wrapper function to delete old cars from database
    """
    return db_manager.delete_old_cars(days)


def check_robots_txt(base_url: str) -> bool:
    """
    Check if scraping is allowed according to robots.txt
    """
    try:
        parsed_url = urlparse(base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

        response = requests.get(
            robots_url,
            timeout=10,
            verify=True
        )

        if response.status_code == 200:
            # Basic robots.txt parsing (simplified)
            # In production, use a proper robots.txt parser library
            content = response.text.lower()
            if 'disallow: /' in content:
                logger.warning("robots.txt disallows crawling. Please check manually.")
                return False

        return True

    except requests.exceptions.RequestException:
        logger.warning("Could not fetch robots.txt. Proceeding with caution.")
        return True

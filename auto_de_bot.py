"""
AutoDE Car Listings Bot - Main Module
A secure and efficient web scraper for auto.de car listings

Version: 2.0.0
Features:
  - Secure request handling with timeout and SSL verification
  - Rate limiting to prevent server overload
  - Input validation and sanitization
  - Retry mechanism with exponential backoff
  - Modular and maintainable code structure
  - Comprehensive error handling and logging
"""

import sys
import time
import signal
from typing import Optional, Dict, Any, List
import requests

# Import custom modules
from common import (
    logger,
    send_error_to_telegram,
    find_endpoint,
    get_vehicle_image_url,
    insert_car_to_database,
    delete_old_cars_from_database,
    retry_on_failure,
    rate_limiter,
    sanitize_string,
    sanitize_number,
    check_robots_txt
)
from config import (
    BASE_URL,
    RESPONSE_IDENTIFIER,
    BOT_NAME,
    BOT_VERSION,
    HEADERS,
    MAX_PAGES,
    REQUEST_TIMEOUT,
    VERIFY_SSL,
    MAIN_LOOP_INTERVAL,
    DELETE_OLD_CARS_DAYS,
    CHECK_ROBOTS_TXT,
    validate_config
)


class AutoDEBot:
    """
    Main bot class for scraping Auto.de car listings
    """

    def __init__(self):
        """Initialize the bot"""
        self.running = True
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'cars_processed': 0,
            'errors': 0
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info(f"{BOT_NAME} v{BOT_VERSION} initialized")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False

    @retry_on_failure(max_retries=3, delay=2, backoff=2)
    def fetch_page_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Fetches data from the API endpoint with proper security measures

        Args:
            endpoint: API endpoint URL

        Returns:
            JSON response data or None if request fails
        """
        try:
            # Apply rate limiting
            rate_limiter.wait_if_needed()

            # Make secure request
            response = requests.get(
                endpoint,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                verify=VERIFY_SSL,
                allow_redirects=True
            )

            # Check response status
            response.raise_for_status()

            # Parse JSON safely
            try:
                data = response.json()
                return data
            except ValueError as e:
                logger.error(f"{BOT_NAME} - Invalid JSON response: {str(e)}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"{BOT_NAME} - Request timeout for endpoint: {endpoint}")
            raise

        except requests.exceptions.SSLError as e:
            logger.error(f"{BOT_NAME} - SSL verification failed: {str(e)}")
            raise

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'Unknown'
            logger.error(f"{BOT_NAME} - HTTP error {status_code}: {str(e)}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"{BOT_NAME} - Request failed: {str(e)}")
            raise

    def extract_car_info(self, car: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extracts and validates car information from raw data

        Args:
            car: Raw car data from API

        Returns:
            Sanitized car information dictionary or None if invalid
        """
        try:
            # Extract and validate car ID
            car_id = car.get('_id')
            if not car_id:
                logger.warning(f"{BOT_NAME} - Car without ID found, skipping")
                return None

            # Sanitize car ID
            car_id = sanitize_string(car_id, max_length=50)

            # Extract main data with safety
            main_data = car.get('mainData', {})
            make = sanitize_string(main_data.get('make', 'Unknown'))
            model = sanitize_string(main_data.get('model', 'Unknown'))
            sub_model = sanitize_string(main_data.get('subModel', ''))

            # Construct model name
            model_parts = [make, model]
            if sub_model and sub_model != 'Unknown':
                model_parts.append(sub_model)
            model_marka = ' '.join(model_parts)

            # Extract price
            price_data = car.get('price', {})
            price = sanitize_number(price_data.get('currentSalesPrice', 0))

            # Extract year
            first_registration_year = sanitize_number(
                main_data.get('firstRegistrationYear', 0)
            )

            # Construct link safely
            link = f"https://www.auto.de/search/vehicle/{car_id}"

            # Get image URL
            main_image_id = car.get('metaData', {}).get('mainImageId')
            image_url = get_vehicle_image_url(car_id, main_image_id)

            # Extract additional information
            transmission = self.get_transmission_type(car)
            fuel_type = self.get_fuel_type(car)
            power_data = self.get_power_data(car)
            co2_emission = self.get_co2_emission(car)
            consumption = self.get_combined_consumption(car)
            mileage = sanitize_number(main_data.get('mileage', 0))

            # Build car information dictionary
            car_info = {
                'ID': car_id,
                'Model and Make': model_marka,
                'Price': price,
                'Link': link,
                'Image': image_url,
                'Company': 'autode',
                'Transmission': transmission,
                'Features': {
                    'mileage_road': mileage,
                    'calendar': first_registration_year,
                    'gas_pump': fuel_type,
                    'speedometer': power_data,
                    'water_drop': consumption,
                    'leaf': co2_emission
                }
            }

            return car_info

        except Exception as e:
            logger.error(f"{BOT_NAME} - Error extracting car info: {str(e)}")
            return None

    def get_transmission_type(self, car: Dict[str, Any]) -> str:
        """Extract and sanitize transmission type"""
        drive_suspension = car.get('driveSuspension', {})
        gearbox = drive_suspension.get('gearbox', 'Unknown')

        transmission_map = {
            'selector_gearbox_manualShift': 'Manual',
            'selector_gearbox_automatic': 'Automatic',
            'selector_gearbox_semiautomatic': 'Semi-Automatic'
        }

        return sanitize_string(transmission_map.get(gearbox, 'Unknown'))

    def get_fuel_type(self, car: Dict[str, Any]) -> str:
        """Extract and sanitize fuel type"""
        consumption = car.get('consumption', {})
        fuel = consumption.get('fuel', 'Unknown')

        fuel_map = {
            'selector_fuel_petrol': 'Petrol',
            'selector_fuel_diesel': 'Diesel',
            'selector_fuel_electric': 'Electric',
            'selector_fuel_hybrid': 'Hybrid',
            'selector_fuel_lpg': 'LPG',
            'selector_fuel_cng': 'CNG'
        }

        return sanitize_string(fuel_map.get(fuel, 'Hybrid'))

    def get_power_data(self, car: Dict[str, Any]) -> str:
        """Extract and sanitize power data"""
        engine_data = car.get('engineData', {})
        power_kw = sanitize_number(engine_data.get('powerKW', 0))
        power_ps = sanitize_number(engine_data.get('powerPS', 0))

        if power_kw and power_ps:
            return f"{power_kw} KW ({power_ps} PS)"
        return "Unknown"

    def get_co2_emission(self, car: Dict[str, Any]) -> str:
        """Extract and sanitize CO2 emission data"""
        env_emissions = car.get('environmentEmissions', {})
        co2 = sanitize_number(env_emissions.get('co2', 0))

        if co2 and co2 > 0:
            return f"{co2} g/km"
        return "Unknown"

    def get_combined_consumption(self, car: Dict[str, Any]) -> str:
        """Extract and sanitize fuel consumption data"""
        consumption = car.get('consumption', {})
        combined = sanitize_number(consumption.get('consumptionCombined', 0))

        if combined and combined > 0:
            return f"{combined} L/100km"
        return "Unknown"

    def process_listing_page(self, endpoint: str) -> int:
        """
        Process a single listing page and extract car information

        Args:
            endpoint: API endpoint to fetch

        Returns:
            Number of cars processed from this page
        """
        try:
            # Fetch page data
            data = self.fetch_page_data(endpoint)
            if not data:
                logger.warning(f"{BOT_NAME} - No data received from endpoint")
                return 0

            # Extract car listings
            car_listings = data.get('data', [])
            if not isinstance(car_listings, list):
                logger.error(f"{BOT_NAME} - Invalid data format received")
                return 0

            # Process each car
            processed_count = 0
            for car in car_listings:
                car_info = self.extract_car_info(car)
                if car_info:
                    if insert_car_to_database(car_info, BOT_NAME):
                        processed_count += 1

            logger.info(f"{BOT_NAME} - Processed {processed_count} cars from page")
            return processed_count

        except Exception as e:
            logger.error(f"{BOT_NAME} - Error processing listing page: {str(e)}")
            return 0

    def check_new_listings(self) -> bool:
        """
        Main function to check for new car listings

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"{BOT_NAME} - Starting new listings check")

            # Check robots.txt if enabled
            if CHECK_ROBOTS_TXT:
                if not check_robots_txt(BASE_URL.format(1)):
                    logger.warning(
                        f"{BOT_NAME} - robots.txt check failed. "
                        "Consider reviewing scraping permissions."
                    )

            total_processed = 0

            # Process each page
            for page in range(1, MAX_PAGES + 1):
                try:
                    logger.info(f"{BOT_NAME} - Processing page {page}/{MAX_PAGES}")

                    url = BASE_URL.format(page)
                    endpoints = find_endpoint(url, RESPONSE_IDENTIFIER, BOT_NAME)

                    if not endpoints:
                        logger.warning(
                            f"{BOT_NAME} - No endpoints found for page {page}"
                        )
                        continue

                    # Process each endpoint found
                    for endpoint in endpoints:
                        count = self.process_listing_page(endpoint)
                        total_processed += count

                except Exception as e:
                    logger.error(
                        f"{BOT_NAME} - Error processing page {page}: {str(e)}"
                    )
                    continue

            self.stats['cars_processed'] += total_processed
            logger.info(
                f"{BOT_NAME} - Completed listings check. "
                f"Total cars processed: {total_processed}"
            )

            return True

        except Exception as e:
            error_msg = f"{BOT_NAME} - Error in check_new_listings: {str(e)}"
            logger.error(error_msg)
            send_error_to_telegram(error_msg)
            return False

    def cleanup_old_listings(self) -> bool:
        """
        Clean up old car listings from database

        Returns:
            True if successful, False otherwise
        """
        try:
            deleted_count = delete_old_cars_from_database(DELETE_OLD_CARS_DAYS)
            if deleted_count > 0:
                logger.info(
                    f"{BOT_NAME} - Cleaned up {deleted_count} old listings"
                )
            return True
        except Exception as e:
            logger.error(f"{BOT_NAME} - Error cleaning up old listings: {str(e)}")
            return False

    def run_cycle(self):
        """Run one complete scraping cycle"""
        self.stats['total_runs'] += 1

        try:
            logger.info(f"{BOT_NAME} - Starting scraping cycle #{self.stats['total_runs']}")

            # Check for new listings
            if self.check_new_listings():
                self.stats['successful_runs'] += 1
            else:
                self.stats['failed_runs'] += 1

            # Cleanup old listings
            self.cleanup_old_listings()

            # Log statistics
            logger.info(
                f"{BOT_NAME} - Cycle complete. Stats: "
                f"Total runs: {self.stats['total_runs']}, "
                f"Successful: {self.stats['successful_runs']}, "
                f"Failed: {self.stats['failed_runs']}, "
                f"Cars processed: {self.stats['cars_processed']}"
            )

        except Exception as e:
            self.stats['failed_runs'] += 1
            self.stats['errors'] += 1
            error_msg = f"{BOT_NAME} - Unexpected error in run cycle: {str(e)}"
            logger.error(error_msg)
            send_error_to_telegram(error_msg)

    def run(self):
        """
        Main bot loop
        Runs continuously until stopped
        """
        logger.info(f"{BOT_NAME} v{BOT_VERSION} started")

        while self.running:
            try:
                self.run_cycle()

                if self.running:
                    logger.info(
                        f"{BOT_NAME} - Waiting {MAIN_LOOP_INTERVAL} seconds "
                        "until next cycle..."
                    )
                    time.sleep(MAIN_LOOP_INTERVAL)

            except KeyboardInterrupt:
                logger.info(f"{BOT_NAME} - Keyboard interrupt received")
                break

            except Exception as e:
                error_msg = f"{BOT_NAME} - Critical error in main loop: {str(e)}"
                logger.error(error_msg)
                send_error_to_telegram(error_msg)

                # Wait before retrying to avoid rapid failure loops
                if self.running:
                    logger.info("Waiting 60 seconds before retry...")
                    time.sleep(60)

        logger.info(f"{BOT_NAME} - Shutting down. Final stats: {self.stats}")


def main():
    """
    Entry point for the application
    """
    try:
        # Print banner
        print("=" * 60)
        print(f"{BOT_NAME} v{BOT_VERSION}")
        print("Secure Auto.de Car Listings Scraper")
        print("=" * 60)
        print()

        # Validate configuration
        logger.info("Validating configuration...")
        validate_config()

        # Create and run bot
        bot = AutoDEBot()
        bot.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        send_error_to_telegram(f"Critical error - Bot stopped: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

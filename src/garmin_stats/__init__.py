import logging
import os
from datetime import date
from functools import cached_property, lru_cache
from typing import Any, Dict, Optional

from garminconnect import Garmin


class GarminStats:
    """Garmin statistics client with caching and lazy initialization."""

    def __init__(self, date_str: Optional[str] = None):
        """
        Initialize GarminStats client.

        Args:
            date_str: Date string in YYYY-MM-DD format. Defaults to today.
        """
        self.date_str = date_str or date.today().strftime("%Y-%m-%d")

    @cached_property
    def client(self) -> Garmin:
        """Get or create Garmin client with lazy initialization and caching."""
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        if not email or not password:
            raise Exception(
                "Garmin credentials not found. Please set environment variables:\n"
                "export GARMIN_EMAIL='your_email@example.com'\n"
                "export GARMIN_PASSWORD='your_password'\n"
                "Or create a .env file with these variables."
            )

        garmin_client = Garmin(email, password)
        garmin_client.login()

        # Save session for future use
        garth_home = os.getenv("GARTH_HOME", "~/.garth")
        garmin_client.garth.dump(garth_home)

        return garmin_client

    @lru_cache(maxsize=32)
    def get_stats(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Garmin stats with caching.

        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses instance date.

        Returns:
            Dictionary containing Garmin stats for the specified date.
        """
        target_date = date_str or self.date_str

        try:
            logging.info(f"Fetching stats for {target_date}")
            return self.client.get_stats(target_date)
        except Exception as e:
            logging.error(f"Error fetching Garmin stats: {e}")
            raise e

    @lru_cache(maxsize=32)
    def get_sleep_data(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sleep data with caching.

        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses instance date.

        Returns:
            Dictionary containing sleep data for the specified date.
        """
        target_date = date_str or self.date_str

        try:
            logging.info(f"Fetching sleep data for {target_date}")
            return self.client.get_sleep_data(target_date)
        except Exception as e:
            logging.error(f"Error fetching sleep data: {e}")
            raise e

    def clear_cache(self):
        """Clear all cached data."""
        self.get_stats.cache_clear()
        self.get_sleep_data.cache_clear()
        logging.info("Cache cleared")

    def update_date(self, date_str: str):
        """
        Update the date and clear cache.

        Args:
            date_str: New date string in YYYY-MM-DD format.
        """
        self.date_str = date_str
        self.clear_cache()
        logging.info(f"Date updated to {date_str}")

    def refresh_data(self, date_str: Optional[str] = None):
        """
        Force refresh of all data for the given date.

        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses instance date.
        """
        target_date = date_str or self.date_str
        logging.info(f"Force refreshing all data for {target_date}")
        self.clear_cache()
        self.get_stats(target_date)
        self.get_sleep_data(target_date)

    @property
    def cache_info(self) -> Dict[str, Any]:
        """Get information about current cache state."""
        return {
            "stats_cache_size": self.get_stats.cache_info().currsize,
            "sleep_cache_size": self.get_sleep_data.cache_info().currsize,
            "stats_cache_hits": self.get_stats.cache_info().hits,
            "sleep_cache_hits": self.get_sleep_data.cache_info().hits,
            "stats_cache_misses": self.get_stats.cache_info().misses,
            "sleep_cache_misses": self.get_sleep_data.cache_info().misses,
            "instance_date": self.date_str,
        }

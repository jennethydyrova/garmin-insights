import logging
import os
from datetime import date
from functools import cached_property
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

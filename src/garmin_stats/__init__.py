import os 
import logging
from datetime import date
from functools import cached_property
from garminconnect import Garmin
from typing import Optional, Dict, Any


class GarminStats:
    """Garmin statistics client with caching and lazy initialization."""
    
    def __init__(self, date_str: Optional[str] = None):
        """
        Initialize GarminStats client.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. Defaults to today.
        """
        self.date_str = date_str or date.today().strftime('%Y-%m-%d')
        self._stats_cache = None
        self._sleep_cache = None
        self._steps_cache = None
        self._cache_date = None
    
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
    
    def _is_cache_valid(self, target_date: str) -> bool:
        """Check if cache is valid for the given date"""
        return self._cache_date == target_date and self._stats_cache is not None
    
    def _is_sleep_cache_valid(self, target_date: str) -> bool:
        """Check if sleep cache is valid for the given date"""
        return self._cache_date == target_date and self._sleep_cache is not None
    
    def _is_steps_cache_valid(self, target_date: str) -> bool:
        """Check if steps cache is valid for the given date"""
        return self._cache_date == target_date and self._steps_cache is not None

    def get_stats(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Garmin stats with caching.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses instance date.
            
        Returns:
            Dictionary containing Garmin stats for the specified date.
        """
        target_date = date_str or self.date_str
        
        # Return cached data if available and for the same date
        if self._is_cache_valid(target_date):
            logging.debug(f"Returning cached stats for {target_date}")
            return self._stats_cache
        
        try:
            logging.info(f"Fetching fresh stats for {target_date}")
            self._stats_cache = self.client.get_stats(target_date)
            self._cache_date = target_date
            return self._stats_cache
        except Exception as e:
            logging.error(f"Error fetching Garmin stats: {e}")
            raise e
    
    def get_steps_data(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get steps data with caching.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses instance date.
            
        Returns:
            Dictionary containing steps data for the specified date.
        """
        target_date = date_str or self.date_str
        
        # Return cached data if available and for the same date
        if self._is_steps_cache_valid(target_date):
            logging.debug(f"Returning cached steps data for {target_date}")
            return self._steps_cache
        
        try:
            logging.info(f"Fetching fresh steps data for {target_date}")
            self._steps_cache = self.client.get_steps_data(target_date)
            self._cache_date = target_date
            return self._steps_cache
        except Exception as e:
            logging.error(f"Error fetching steps data: {e}")
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
        
        # Return cached data if available and for the same date
        if self._is_sleep_cache_valid(target_date):
            logging.debug(f"Returning cached sleep data for {target_date}")
            return self._sleep_cache
        
        try:
            logging.info(f"Fetching fresh sleep data for {target_date}")
            self._sleep_cache = self.client.get_sleep_data(target_date)
            self._cache_date = target_date
            return self._sleep_cache
        except Exception as e:
            logging.error(f"Error fetching sleep data: {e}")
            raise e
    
    def clear_cache(self):
        """Clear all cached data."""
        self._stats_cache = None
        self._sleep_cache = None
        self._steps_cache = None
        self._cache_date = None
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
        self.get_steps_data(target_date)
    
    @property
    def cache_info(self) -> Dict[str, Any]:
        """Get information about current cache state."""
        return {
            "cache_date": self._cache_date,
            "has_stats_cache": self._stats_cache is not None,
            "has_sleep_cache": self._sleep_cache is not None,
            "has_steps_cache": self._steps_cache is not None,
            "instance_date": self.date_str
        }
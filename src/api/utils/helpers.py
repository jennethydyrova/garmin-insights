import logging
from fastapi import HTTPException

from ...garmin_stats import GarminStats
from .classes import ActivityData, SleepData
from .classes import Metric

def validate_retrieved_data(data: ActivityData | SleepData, field_name: str, endpoint_name: str) -> None:
    """Validate that required retrieved data is available and non-zero"""
    field_value = getattr(data, field_name)
    if field_value == 0:
        logging.error(f"Field {field_name} is zero for {endpoint_name}")
        raise HTTPException(
            status_code=404,
            detail=f"No {field_name} data available for {endpoint_name}"
        )

def build_metric_response(value: float, unit: str, description: str) -> Metric:
    return Metric(metric=round(value, 2), unit=unit, description=description)

def get_garmin_data_dependency(data_type: str = "sleep"):
    """Factory function that returns a dependency for specific data type"""
    async def dependency() -> dict:
        """Dependency to get Garmin data with proper error handling"""
        try:
            garmin = GarminStats()
            
            # Get data based on type
            match data_type:
                case "sleep":
                    data = garmin.get_sleep_data()
                case "activity":
                    data = garmin.get_stats()
                case _:
                    raise HTTPException(status_code=400, detail=f"Invalid data type: {data_type}")
            
            if not data:
                raise HTTPException(
                    status_code=503, 
                    detail=f"No {data_type} data available from Garmin API"
                )
            return data
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Unable to fetch Garmin {data_type} data: {str(e)}"
            )
    
    return dependency

def convert_sleep_stage_to_percentage(data: SleepData) -> dict:
    """Convert sleep stage data to percentage"""
    return {
        'deep': convert_to_percentage(data.deep, data.sleep_time),
        'light': convert_to_percentage(data.light, data.sleep_time),
        'rem': convert_to_percentage(data.rem, data.sleep_time)
    }

def convert_seconds_to_hours(seconds: int) -> float:
    """Convert seconds to hours"""
    return seconds / 3600

def convert_to_percentage(value: float, total: float) -> float:
    """Convert a value to a percentage"""
    return (value / total) * 100

def convert_meters_to_kilometers(meters: float) -> float:
    """Convert meters to kilometers"""
    return meters / 1000

def convert_seconds_to_minutes(seconds: float) -> float:
    """Convert seconds to minutes"""
    return seconds / 60
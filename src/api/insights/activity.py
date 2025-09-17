import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from ...garmin_stats import GarminStats

router = APIRouter(prefix="/insights/activity", tags=["activity"])

class ActivityMetric(BaseModel):
    """Activity metric response model"""
    metric: float = Field(..., description="The calculated metric value")
    unit: str = Field(..., description="Unit of measurement")
    description: str = Field(..., description="Detailed description of the metric")

def build_metric_response(value: float, unit: str, description: str) -> ActivityMetric:
    return ActivityMetric(metric=round(value, 2), unit=unit, description=description)

class ActivityData(BaseModel):
    """Extracted activity data"""
    total_steps: int = 0
    daily_step_goal: int = 0
    total_kilocalories: int = 0
    total_distance_meters: int = 0
    sedentary_seconds: int = 0
    active_kilocalories: int = 0
    active_seconds: int = 0

async def get_activity_data_dependency() -> dict:
    """Dependency to get activity data with proper error handling"""
    try:
        garmin_stats = GarminStats()
        activity_data = garmin_stats.get_stats()
        if not activity_data:
            logging.error("Activity data is empty from Garmin API")
            raise HTTPException(
                status_code=503, 
                detail="No activity data available from Garmin API"
            )
        return activity_data
    except Exception as e:
        logging.error(f"Unable to fetch Garmin activity data: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Unable to fetch Garmin activity data: {str(e)}"
        )

def extract_activity_data(activity_data: dict) -> ActivityData:
    """Extract and validate activity data from Garmin API response"""
    
    return ActivityData(
        total_steps=activity_data.get('totalSteps', 0),
        daily_step_goal=activity_data.get('dailyStepGoal', 0),
        total_kilocalories=activity_data.get('totalKilocalories', 0),
        total_distance_meters=activity_data.get('totalDistanceMeters', 0),
        sedentary_seconds=activity_data.get('sedentarySeconds', 0),
        active_kilocalories=activity_data.get('activeKilocalories', 0),
        active_seconds=activity_data.get('activeSeconds', 0),
    )

def validate_activity_data(data: ActivityData, field_name: str, endpoint_name: str) -> None:
    """Validate that required activity data is available and non-zero"""
    field_value = getattr(data, field_name)
    if field_value == 0:
        logging.error(f"Field {field_name} is zero for {endpoint_name}")
        raise HTTPException(
            status_code=404,
            detail=f"No {field_name} data available for {endpoint_name}"
        )

@router.get(
    "/health",
    summary="Activity API health check",
    description="Check if activity data is available from Garmin API"
)
async def activity_health_check() -> dict:
    """Health check endpoint for activity API"""
    try:
        garmin_stats = GarminStats()
        activity_data = garmin_stats.get_stats()
        if activity_data:
            return {
                "status": "healthy",
                "message": "Activity data available",
                "data_keys": list(activity_data.keys()) if isinstance(activity_data, dict) else [],
                "cache_info": garmin_stats.cache_info
            }
        else:
            return {
                "status": "unhealthy",
                "message": "No activity data available"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Error fetching activity data: {str(e)}"
        }

@router.get(
    "/step_goal_percent",
    response_model=ActivityMetric,
    summary="Get step goal percentage",
    description="Calculate percentage of daily step goal achieved"
)
async def get_step_goal_percent(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate step goal percentage: (totalSteps / dailyStepGoal) * 100"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "daily_step_goal", "step goal percent")
    
    step_goal_percent = (data.total_steps / data.daily_step_goal) * 100
    
    return build_metric_response(
        value=step_goal_percent,
        unit="%",
        description=f"Step goal progress: {step_goal_percent:.2f}% ({data.total_steps:,} / {data.daily_step_goal:,} steps)"
    )
    
@router.get(
    "/calories_per_step",
    response_model=ActivityMetric,
    summary="Get calories per step",
    description="Calculate average calories burned per step"
)
async def get_calories_per_step(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate calories per step: totalKilocalories / totalSteps"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "total_steps", "calories per step")
    
    calories_per_step = data.total_kilocalories / data.total_steps
    
    return build_metric_response(
        value=calories_per_step,
        unit="kcal/step",
        description=f"Average calories per step: {calories_per_step:.2f} kcal/step"
    )

@router.get(
    "/calories_per_km",
    response_model=ActivityMetric,
    summary="Get calories per kilometer",
    description="Calculate average calories burned per kilometer"
)
async def get_calories_per_km(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate calories per km: totalKilocalories / (totalDistanceMeters / 1000)"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "total_distance_meters", "calories per km")
    
    distance_km = data.total_distance_meters / 1000
    calories_per_km = data.total_kilocalories / distance_km
    
    return build_metric_response(
        value=calories_per_km,
        unit="kcal/km",
        description=f"Average calories per kilometer: {calories_per_km:.2f} kcal/km"
    )

@router.get(
    "/stride_length",
    response_model=ActivityMetric,
    summary="Get average stride length",
    description="Calculate average stride length in meters per step"
)
async def get_stride_length(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate stride length: totalDistanceMeters / totalSteps"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "total_steps", "stride length")
    
    stride_length = data.total_distance_meters / data.total_steps
    
    return build_metric_response(
        value=stride_length,
        unit="m/step",
        description=f"Average stride length: {stride_length:.2f} meters per step"
    )

@router.get(
    "/sedentary_ratio",
    response_model=ActivityMetric,
    summary="Get sedentary minutes ratio",
    description="Calculate ratio of sedentary time to total time elapsed today"
)
async def get_sedentary_minutes(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate sedentary minutes ratio: sedentaryMinutes / totalMinutes till now"""
    
    data = extract_activity_data(activity_data)
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute
    
    if minutes_since_midnight == 0:
        minutes_since_midnight = 1  # Avoid division by zero
    
    sedentary_ratio = (data.sedentary_seconds / 60) / minutes_since_midnight
    
    return build_metric_response(
        value=sedentary_ratio,
        unit="ratio",
        description=f"Sedentary time ratio: {sedentary_ratio:.2f} ({data.sedentary_seconds // 60} min sedentary / {minutes_since_midnight} min elapsed)"
    )

@router.get(
    "/steps_per_km",
    response_model=ActivityMetric,
    summary="Get steps per kilometer",
    description="Calculate average number of steps per kilometer"
)
async def get_steps_per_km(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate steps per km: totalSteps / (totalDistanceMeters/1000)"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "total_distance_meters", "steps per km")
    
    distance_km = data.total_distance_meters / 1000
    steps_per_km = data.total_steps / distance_km
    
    return build_metric_response(
        value=steps_per_km,
        unit="steps/km",
        description=f"Average steps per kilometer: {steps_per_km:.2f} steps/km"
    )

@router.get(
    "/active_minutes_percent",
    response_model=ActivityMetric,
    summary="Get active minutes percentage",
    description="Calculate percentage of time spent in active minutes today"
)
async def get_active_minutes_percent(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate active minutes percentage: activeMinutes / totalMinutes * 100"""
    
    data = extract_activity_data(activity_data)
    
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute

    if minutes_since_midnight == 0:
        minutes_since_midnight = 1  # Avoid division by zero
    
    active_percent = (data.active_seconds / 60) / minutes_since_midnight * 100
    
    return build_metric_response(
        value=active_percent,
        unit="%",
        description=f"Active time percentage: {active_percent:.2f}% ({data.active_seconds // 60} min active / {minutes_since_midnight} min elapsed)"
    )

@router.get(
    "/calories_per_active_min",
    response_model=ActivityMetric,
    summary="Get calories per active minute",
    description="Calculate average calories burned per active minute"
)
async def get_calories_per_active_min(
    activity_data: dict = Depends(get_activity_data_dependency)
) -> ActivityMetric:
    """Calculate calories per active minute: activeKilocalories / activeMinutes"""
    
    data = extract_activity_data(activity_data)
    validate_activity_data(data, "active_seconds", "calories per active minute")
    
    active_minutes = data.active_seconds / 60
    calories_per_active_min = data.active_kilocalories / active_minutes
    
    return build_metric_response(
        value=calories_per_active_min,
        unit="kcal/min",
        description=f"Average calories per active minute: {calories_per_active_min:.2f} kcal/min"
    )
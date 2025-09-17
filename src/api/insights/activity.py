import logging

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from ...garmin_stats import GarminStats
from ..utils import Metric, ActivityData, validate_retrieved_data, convert_to_percentage, convert_meters_to_kilometers, convert_seconds_to_minutes, build_metric_response, get_garmin_data_dependency

router = APIRouter(prefix="/insights/activity", tags=["activity"])

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

@router.get(
    "/step_goal_percent",
    response_model=Metric,
    summary="Get step goal percentage",
    description="Calculate percentage of daily step goal achieved"
)
async def get_step_goal_percent(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate step goal percentage: (totalSteps / dailyStepGoal) * 100"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "daily_step_goal", "step goal percent")
    
    step_goal_percent = convert_to_percentage(data.total_steps, data.daily_step_goal)
    
    return build_metric_response(
        value=step_goal_percent,
        unit="%",
        description=f"Step goal progress: {step_goal_percent:.2f}% ({data.total_steps:,} / {data.daily_step_goal:,} steps)"
    )
    
@router.get(
    "/calories_per_step",
    response_model=Metric,
    summary="Get calories per step",
    description="Calculate average calories burned per step"
)
async def get_calories_per_step(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate calories per step: totalKilocalories / totalSteps"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "total_steps", "calories per step")
    
    calories_per_step = data.total_kilocalories / data.total_steps
    
    return build_metric_response(
        value=calories_per_step,
        unit="kcal/step",
        description=f"Average calories per step: {calories_per_step:.2f} kcal/step"
    )

@router.get(
    "/calories_per_km",
    response_model=Metric,
    summary="Get calories per kilometer",
    description="Calculate average calories burned per kilometer"
)
async def get_calories_per_km(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate calories per km: totalKilocalories / (totalDistanceMeters / 1000)"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "total_distance_meters", "calories per km")
    
    distance_km = convert_meters_to_kilometers(data.total_distance_meters)
    calories_per_km = data.total_kilocalories / distance_km
    
    return build_metric_response(
        value=calories_per_km,
        unit="kcal/km",
        description=f"Average calories per kilometer: {calories_per_km:.2f} kcal/km"
    )

@router.get(
    "/stride_length",
    response_model=Metric,
    summary="Get average stride length",
    description="Calculate average stride length in meters per step"
)
async def get_stride_length(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate stride length: totalDistanceMeters / totalSteps"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "total_steps", "stride length")
    
    stride_length = data.total_distance_meters / data.total_steps
    
    return build_metric_response(
        value=stride_length,
        unit="m/step",
        description=f"Average stride length: {stride_length:.2f} meters per step"
    )

@router.get(
    "/sedentary_ratio",
    response_model=Metric,
    summary="Get sedentary minutes ratio",
    description="Calculate ratio of sedentary time to total time elapsed today"
)
async def get_sedentary_minutes(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate sedentary minutes ratio: sedentaryMinutes / totalMinutes till now"""
    
    data = extract_activity_data(activity_data)
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute
    
    if minutes_since_midnight == 0:
        minutes_since_midnight = 1  # Avoid division by zero
    
    sedentary_ratio = (convert_seconds_to_minutes(data.sedentary_seconds)) / minutes_since_midnight
    
    return build_metric_response(
        value=sedentary_ratio,
        unit="ratio",
        description=f"Sedentary time ratio: {sedentary_ratio:.2f} ({data.sedentary_seconds // 60} min sedentary / {minutes_since_midnight} min elapsed)"
    )

@router.get(
    "/steps_per_km",
    response_model=Metric,
    summary="Get steps per kilometer",
    description="Calculate average number of steps per kilometer"
)
async def get_steps_per_km(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate steps per km: totalSteps / (totalDistanceMeters/1000)"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "total_distance_meters", "steps per km")
    
    distance_km = convert_meters_to_kilometers(data.total_distance_meters)
    steps_per_km = data.total_steps / distance_km
    
    return build_metric_response(
        value=steps_per_km,
        unit="steps/km",
        description=f"Average steps per kilometer: {steps_per_km:.2f} steps/km"
    )

@router.get(
    "/active_minutes_percent",
    response_model=Metric,
    summary="Get active minutes percentage",
    description="Calculate percentage of time spent in active minutes today"
)
async def get_active_minutes_percent(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate active minutes percentage: activeMinutes / totalMinutes * 100"""
    
    data = extract_activity_data(activity_data)
    
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute

    if minutes_since_midnight == 0:
        minutes_since_midnight = 1  # Avoid division by zero
    active_minutes = convert_seconds_to_minutes(data.active_seconds)
    active_percent = convert_to_percentage(active_minutes, minutes_since_midnight)
    
    return build_metric_response(
        value=active_percent,
        unit="%",
        description=f"Active time percentage: {active_percent:.2f}% ({data.active_seconds // 60} min active / {minutes_since_midnight} min elapsed)"
    )

@router.get(
    "/calories_per_active_min",
    response_model=Metric,
    summary="Get calories per active minute",
    description="Calculate average calories burned per active minute"
)
async def get_calories_per_active_min(
    activity_data: dict = Depends(get_garmin_data_dependency("activity"))
) -> Metric:
    """Calculate calories per active minute: activeKilocalories / activeMinutes"""
    
    data = extract_activity_data(activity_data)
    validate_retrieved_data(data, "active_seconds", "calories per active minute")
    
    active_minutes = convert_seconds_to_minutes(data.active_seconds)
    calories_per_active_min = data.active_kilocalories / active_minutes
    
    return build_metric_response(
        value=calories_per_active_min,
        unit="kcal/min",
        description=f"Average calories per active minute: {calories_per_active_min:.2f} kcal/min"
    )
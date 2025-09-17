from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Metric(BaseModel):
    """Generic metric response model"""
    metric: float = Field(..., description="The calculated metric value")
    unit: str = Field(..., description="Unit of measurement")
    description: str = Field(..., description="Detailed description of the metric")


class ActivityData(BaseModel):
    """Extracted activity data"""
    total_steps: int = 0
    daily_step_goal: int = 0
    total_kilocalories: int = 0
    total_distance_meters: int = 0
    sedentary_seconds: int = 0
    active_kilocalories: int = 0
    active_seconds: int = 0


class SleepData(BaseModel):
    """Extracted sleep stage data"""
    deep: int = 0
    light: int = 0
    rem: int = 0
    sleep_time: int = 0
    awakenings: Optional[int] = None
    awake_duration: int = 0
    sleep_end: Optional[int] = None
    sleep_start: Optional[int] = None
    sleep_need: Optional[Dict[str, Any]] = None

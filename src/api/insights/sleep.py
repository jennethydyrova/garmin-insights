from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from ...garmin_stats import GarminStats

router = APIRouter(prefix="/insights/sleep", tags=["sleep"])

class SleepMetric(BaseModel):
    """Sleep metric response model"""
    metric: float = Field(..., description="The calculated metric value")
    unit: str = Field(..., description="Unit of measurement")
    description: str = Field(..., description="Detailed description of the metric")

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

async def get_sleep_data_dependency() -> dict:
    """Dependency to get sleep data with proper error handling"""
    try:
        garmin_stats = GarminStats()
        sleep_data = garmin_stats.get_sleep_data()
        if not sleep_data:
            raise HTTPException(
                status_code=503, 
                detail="No sleep data available from Garmin API"
            )
        return sleep_data
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Unable to fetch Garmin sleep data: {str(e)}"
        )

def extract_sleep_stage_data(sleep_data: dict) -> SleepData:
    """Extract and validate sleep stage data from nested structure"""
    daily_sleep = sleep_data.get('dailySleepDTO', {})
    
    return SleepData(
        deep=daily_sleep.get('deepSleepSeconds', 0),
        light=daily_sleep.get('lightSleepSeconds', 0),
        rem=daily_sleep.get('remSleepSeconds', 0),
        sleep_time=daily_sleep.get('sleepTimeSeconds', 0),
        awakenings=daily_sleep.get('awakeCount'),
        awake_duration=daily_sleep.get('awakeSleepSeconds', 0),
        sleep_end=daily_sleep.get('sleepEndTimestampGMT', 0),
        sleep_start=daily_sleep.get('sleepStartTimestampGMT', 0),
        sleep_need=daily_sleep.get('sleepNeed', None)
    )

def validate_sleep_time(sleep_time: int, endpoint_name: str) -> None:
    """Validate that sleep time is available and non-zero"""
    if sleep_time == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No sleep time data available for {endpoint_name}"
        )

def calculate_sleep_stage_percent(data: SleepData, stage_name: str, stage_seconds: int) -> SleepMetric:
    """Calculate sleep stage percentage with analysis"""
    validate_sleep_time(data.sleep_time, f"{stage_name} sleep percent")
    
    stage_percent = (stage_seconds / data.sleep_time) * 100
    analysis = analyze_stage_composition(data)
    
    return SleepMetric(
        metric=round(stage_percent, 2),
        unit="%",
        description=analysis
    )

def analyze_stage_composition(data: SleepData) -> str:
    """Analyze sleep stage composition vs optimal ranges"""
    if data.sleep_time == 0:
        return "No sleep data available"
    
    # Calculate actual percentages
    deep_percent = (data.deep / data.sleep_time) * 100
    light_percent = (data.light / data.sleep_time) * 100
    rem_percent = (data.rem / data.sleep_time) * 100
    
    # Optimal ranges (based on sleep science)
    OPTIMAL_RANGES = {
        'deep': (16, 33),
        'light': (30, 64),
        'rem': (21, 31)
    }
    
    def analyze_stage(stage_name: str, percent: float, min_val: int, max_val: int) -> str:
        """Analyze individual sleep stage"""
        gap_to_min = percent - min_val
        
        if gap_to_min < 0:
            gap_minutes = (abs(gap_to_min) / 100) * (data.sleep_time / 60)
            return f"{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%) - {abs(gap_to_min):.1f}pp below minimum ({gap_minutes:.1f} min deficit)"
        elif percent > max_val:
            return f"{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%) - {percent - max_val:.1f}pp above maximum"
        else:
            return f"{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%) - within optimal range"
    
    # Build analysis for each stage
    analyses = [
        analyze_stage("Deep", deep_percent, *OPTIMAL_RANGES['deep']),
        analyze_stage("Light", light_percent, *OPTIMAL_RANGES['light']),
        analyze_stage("REM", rem_percent, *OPTIMAL_RANGES['rem'])
    ]
    
    return " | ".join(analyses)

@router.get(
    "/health",
    summary="Sleep API health check",
    description="Check if sleep data is available from Garmin API"
)
async def sleep_health_check() -> dict:
    """Health check endpoint for sleep API"""
    try:
        garmin_stats = GarminStats()
        sleep_data = garmin_stats.get_sleep_data()
        if sleep_data:
            return {
                "status": "healthy",
                "message": "Sleep data available",
                "data_keys": list(sleep_data.keys()) if isinstance(sleep_data, dict) else [],
                "cache_info": garmin_stats.cache_info
            }
        else:
            return {
                "status": "unhealthy",
                "message": "No sleep data available"
            }
    except Exception as e:
        return {
                "status": "unhealthy",
                "message": f"Error fetching sleep data: {str(e)}"
            }

@router.get(
    "/time_in_bed", 
    response_model=SleepMetric,
    summary="Get time in bed",
    description="Calculate total time spent in bed based on sleep start and end timestamps"
)
async def get_time_in_bed(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Get time in bed in seconds"""
    
    data = extract_sleep_stage_data(sleep_data)
    
    if not data.sleep_end or not data.sleep_start:
        raise HTTPException(
            status_code=404, 
            detail="Sleep timestamp data not available"
        )

    # Calculate time in bed (convert from milliseconds to seconds)
    time_in_bed_seconds = (data.sleep_end - data.sleep_start) / 1000
    time_in_bed_hours = time_in_bed_seconds / 3600

    return SleepMetric(
        metric=round(time_in_bed_seconds, 2),
        unit="seconds",
        description=f"Total time in bed: {time_in_bed_seconds:.2f} seconds ({time_in_bed_hours:.2f} hours)"
    )

@router.get(
    "/sleep_efficiency",
    response_model=SleepMetric,
    summary="Get sleep efficiency",
    description="Calculate sleep efficiency as percentage of time in bed spent actually sleeping"
)
async def get_sleep_efficiency(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate sleep efficiency percentage"""

    data = extract_sleep_stage_data(sleep_data)
    
    if not data.sleep_time or not data.sleep_end or not data.sleep_start:
        raise HTTPException(
            status_code=404,
            detail="Required sleep data not available"
        )
    
    # Calculate time in bed
    time_in_bed_seconds = (data.sleep_end - data.sleep_start) / 1000
    
    if time_in_bed_seconds == 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid sleep data: time in bed is zero"
        )
    
    # Calculate efficiency percentage
    efficiency_percent = (data.sleep_time / time_in_bed_seconds) * 100
    
    return SleepMetric(
        metric=round(efficiency_percent, 2),
        unit="%",
        description=f"Sleep efficiency: {efficiency_percent:.2f}% of time in bed spent sleeping"
    )

@router.get(
    "/awakenings_per_hour",
    response_model=SleepMetric,
    summary="Get awakenings per hour",
    description="Calculate average number of awakenings per hour of sleep"
)
async def get_awakenings_per_hour(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate awakenings per hour: awakeCount / (sleepTimeSeconds/3600)"""
    
    data = extract_sleep_stage_data(sleep_data)
    validate_sleep_time(data.sleep_time, "awakenings per hour")
    
    awakenings_per_hour = data.awakenings / (data.sleep_time / 3600)
    
    return SleepMetric(
        metric=round(awakenings_per_hour, 2),
        unit="awakenings/hour",
        description=f"Average {awakenings_per_hour:.2f} awakenings per hour of sleep"
    )

@router.get(
    "/deep_sleep_percent",
    response_model=SleepMetric,
    summary="Get deep sleep percentage",
    description="Calculate deep sleep as percentage of total sleep time with optimal range analysis"
)
async def get_deep_sleep_percent(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate deep sleep percent: deepSleepSeconds / sleepTimeSeconds * 100"""
    
    data = extract_sleep_stage_data(sleep_data)
    return calculate_sleep_stage_percent(data, "Deep", data.deep)

@router.get(
    "/rem_sleep_percent",
    response_model=SleepMetric,
    summary="Get REM sleep percentage",
    description="Calculate REM sleep as percentage of total sleep time with optimal range analysis"
)
async def get_rem_sleep_percent(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate REM sleep percent: remSleepSeconds / sleepTimeSeconds * 100"""
    
    data = extract_sleep_stage_data(sleep_data)
    return calculate_sleep_stage_percent(data, "REM", data.rem)

@router.get(
    "/light_sleep_percent",
    response_model=SleepMetric,
    summary="Get light sleep percentage",
    description="Calculate light sleep as percentage of total sleep time with optimal range analysis"
)
async def get_light_sleep_percent(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate light sleep percent: lightSleepSeconds / sleepTimeSeconds * 100"""
    
    data = extract_sleep_stage_data(sleep_data)
    return calculate_sleep_stage_percent(data, "Light", data.light)

@router.get(
    "/sleep_fragmentation_index",
    response_model=SleepMetric,
    summary="Get sleep fragmentation index",
    description="Calculate sleep fragmentation based on awakenings or awake duration (lower is better)"
)
async def get_sleep_fragmentation_index(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate sleep fragmentation: awakenings / ((deep + light + rem)/3600) or awakeDurationInSeconds"""
    
    data = extract_sleep_stage_data(sleep_data)
    
    total_sleep_hours = (data.deep + data.light + data.rem) / 3600
    
    if total_sleep_hours == 0:
        raise HTTPException(
            status_code=404,
            detail="No sleep time data available"
        )
    
    if data.awakenings is not None:
        # Use awakenings count if available
        fragmentation = data.awakenings / total_sleep_hours
    else:
        # Use awake duration as fallback
        fragmentation = (data.awake_duration / 3600) / total_sleep_hours
    
    return SleepMetric(
        metric=round(fragmentation, 2),
        unit="index",
        description=f"Sleep fragmentation index: {fragmentation:.2f} (lower is better)"
    )

@router.get(
    "/stage_composition_analysis",
    response_model=SleepMetric,
    summary="Get sleep stage composition analysis",
    description="Get detailed analysis of sleep stage composition vs optimal ranges with overall quality score"
)
async def get_stage_composition_analysis(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Get detailed analysis of sleep stage composition vs optimal ranges"""
    
    data = extract_sleep_stage_data(sleep_data)
    validate_sleep_time(data.sleep_time, "stage composition analysis")
    
    analysis = analyze_stage_composition(data)
    
    # Calculate overall sleep quality score
    deep_percent = (data.deep / data.sleep_time) * 100
    light_percent = (data.light / data.sleep_time) * 100
    rem_percent = (data.rem / data.sleep_time) * 100
    
    # Simple scoring: 100 - sum of deviations from optimal ranges
    deep_score = max(0, 100 - abs(deep_percent - 24.5) * 2)  
    light_score = max(0, 100 - abs(light_percent - 47) * 1.5) 
    rem_score = max(0, 100 - abs(rem_percent - 26) * 2) 
    
    overall_score = (deep_score + light_score + rem_score) / 3
    
    return SleepMetric(
        metric=round(overall_score, 2),
        unit="score (0-100)",
        description=f"Overall sleep stage quality: {overall_score:.2f}/100 | {analysis}"
    )

@router.get(
    "/sleep_need_gap_minutes",
    response_model=SleepMetric,
    summary="Get sleep need gap",
    description="Calculate the difference between actual sleep and baseline sleep need in minutes"
)
async def get_sleep_need_gap_minutes(
    sleep_data: dict = Depends(get_sleep_data_dependency)
) -> SleepMetric:
    """Calculate sleep need gap minutes: sleepNeed.actual - sleepNeed.baseline"""
    
    data = extract_sleep_stage_data(sleep_data)
    sleep_need = data.sleep_need
    
    if not sleep_need:
        raise HTTPException(
            status_code=404,
            detail="No sleep need data available"
        )

    gap_minutes = sleep_need.get('actual', 0) - sleep_need.get('baseline', 0)
    
    return SleepMetric(
        metric=round(gap_minutes, 2),
        unit="minutes",
        description=f"Sleep need gap: {gap_minutes:.2f} minutes (positive = deficit, negative = surplus)"
    )  
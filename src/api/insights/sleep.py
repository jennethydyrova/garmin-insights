from fastapi import APIRouter, Depends, HTTPException

from ..utils import (
    Metric,
    SleepData,
    build_metric_response,
    convert_seconds_to_hours,
    convert_seconds_to_minutes,
    convert_sleep_stage_to_percentage,
    convert_to_percentage,
    get_garmin_data_dependency,
    validate_retrieved_data,
)

router = APIRouter(prefix="/insights/sleep", tags=["sleep"])


def extract_sleep_stage_data(sleep_data: dict) -> SleepData:
    """Extract and validate sleep stage data from nested structure"""
    daily_sleep = sleep_data.get("dailySleepDTO", {})

    return SleepData(
        deep=daily_sleep.get("deepSleepSeconds", 0),
        light=daily_sleep.get("lightSleepSeconds", 0),
        rem=daily_sleep.get("remSleepSeconds", 0),
        sleep_time=daily_sleep.get("sleepTimeSeconds", 0),
        awakenings=daily_sleep.get("awakeCount"),
        awake_duration=daily_sleep.get("awakeSleepSeconds", 0),
        sleep_end=daily_sleep.get("sleepEndTimestampGMT", 0),
        sleep_start=daily_sleep.get("sleepStartTimestampGMT", 0),
        sleep_need=daily_sleep.get("sleepNeed", None),
    )


def analyze_stage_composition(data: SleepData) -> str:
    """Analyze sleep stage composition vs optimal ranges"""
    if data.sleep_time == 0:
        return "No sleep data available"

    percentages = convert_sleep_stage_to_percentage(data)
    deep_percent = percentages["deep"]
    light_percent = percentages["light"]
    rem_percent = percentages["rem"]

    # Optimal ranges (based on sleep science)
    OPTIMAL_RANGES = {"deep": (16, 33), "light": (30, 64), "rem": (21, 31)}

    def analyze_stage(
        stage_name: str, percent: float, min_val: int, max_val: int
    ) -> str:
        """Analyze individual sleep stage"""
        gap_to_min = percent - min_val

        if gap_to_min < 0:
            gap_minutes = (abs(gap_to_min) / 100) * (
                convert_seconds_to_minutes(data.sleep_time)
            )
            return f"""{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%)
                - {abs(gap_to_min):.1f}pp below minimum ({gap_minutes:.1f} min deficit)"""
        elif percent > max_val:
            return f"""{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%)
                - {percent - max_val:.1f}pp above maximum"""
        else:
            return f"{stage_name} sleep: {percent:.1f}% (optimal: {min_val}-{max_val}%) - within optimal range"

    # Build analysis for each stage
    analyses = [
        analyze_stage("Deep", deep_percent, *OPTIMAL_RANGES["deep"]),
        analyze_stage("Light", light_percent, *OPTIMAL_RANGES["light"]),
        analyze_stage("REM", rem_percent, *OPTIMAL_RANGES["rem"]),
    ]

    return " | ".join(analyses)


@router.get(
    "/time_in_bed",
    response_model=Metric,
    summary="Get time in bed",
    description="Calculate total time spent in bed based on sleep start and end timestamps",
)
async def get_time_in_bed(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Get time in bed in seconds"""

    data = extract_sleep_stage_data(sleep_data)

    if not data.sleep_end or not data.sleep_start:
        raise HTTPException(
            status_code=404, detail="Sleep timestamp data not available"
        )

    # Calculate time in bed (convert from milliseconds to seconds)
    time_in_bed_seconds = (data.sleep_end - data.sleep_start) / 1000
    time_in_bed_hours = convert_seconds_to_hours(time_in_bed_seconds)

    return Metric(
        metric=round(time_in_bed_seconds, 2),
        unit="seconds",
        description=f"Total time in bed: {time_in_bed_seconds:.2f} seconds ({time_in_bed_hours:.2f} hours)",
    )


@router.get(
    "/sleep_efficiency",
    response_model=Metric,
    summary="Get sleep efficiency",
    description="Calculate sleep efficiency as percentage of time in bed spent actually sleeping",
)
async def get_sleep_efficiency(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate sleep efficiency percentage"""

    data = extract_sleep_stage_data(sleep_data)

    if not data.sleep_time or not data.sleep_end or not data.sleep_start:
        raise HTTPException(status_code=404, detail="Required sleep data not available")

    # Calculate time in bed
    time_in_bed_seconds = (data.sleep_end - data.sleep_start) / 1000

    if time_in_bed_seconds == 0:
        raise HTTPException(
            status_code=400, detail="Invalid sleep data: time in bed is zero"
        )

    # Calculate efficiency percentage
    efficiency_percent = convert_to_percentage(data.sleep_time, time_in_bed_seconds)

    return build_metric_response(
        value=round(efficiency_percent, 2),
        unit="%",
        description=f"Sleep efficiency: {efficiency_percent:.2f}% of time in bed spent sleeping",
    )


@router.get(
    "/awakenings_per_hour",
    response_model=Metric,
    summary="Get awakenings per hour",
    description="Calculate average number of awakenings per hour of sleep",
)
async def get_awakenings_per_hour(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate awakenings per hour: awakeCount / (sleepTimeSeconds/3600)"""

    data = extract_sleep_stage_data(sleep_data)
    validate_retrieved_data(data, "sleep_time", "awakenings per hour")

    awakenings_per_hour = data.awakenings / convert_seconds_to_hours(data.sleep_time)

    return build_metric_response(
        value=round(awakenings_per_hour, 2),
        unit="awakenings/hour",
        description=f"Average {awakenings_per_hour:.2f} awakenings per hour of sleep",
    )


@router.get(
    "/deep_sleep_percent",
    response_model=Metric,
    summary="Get deep sleep percentage",
    description="Calculate deep sleep as percentage of total sleep time with optimal range analysis",
)
async def get_deep_sleep_percent(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate deep sleep percent: deepSleepSeconds / sleepTimeSeconds * 100"""

    data = extract_sleep_stage_data(sleep_data)
    deep_sleep_percent = convert_sleep_stage_to_percentage(data)["deep"]

    return build_metric_response(
        value=deep_sleep_percent,
        unit="%",
        description=f"Deep sleep percent: {deep_sleep_percent:.2f}%",
    )


@router.get(
    "/rem_sleep_percent",
    response_model=Metric,
    summary="Get REM sleep percentage",
    description="Calculate REM sleep as percentage of total sleep time with optimal range analysis",
)
async def get_rem_sleep_percent(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate REM sleep percent: remSleepSeconds / sleepTimeSeconds * 100"""

    data = extract_sleep_stage_data(sleep_data)
    rem_sleep_percent = convert_sleep_stage_to_percentage(data)["rem"]
    return build_metric_response(
        value=rem_sleep_percent,
        unit="%",
        description=f"REM sleep percent: {rem_sleep_percent:.2f}%",
    )


@router.get(
    "/light_sleep_percent",
    response_model=Metric,
    summary="Get light sleep percentage",
    description="Calculate light sleep as percentage of total sleep time with optimal range analysis",
)
async def get_light_sleep_percent(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate light sleep percent: lightSleepSeconds / sleepTimeSeconds * 100"""

    data = extract_sleep_stage_data(sleep_data)
    light_sleep_percent = convert_sleep_stage_to_percentage(data)["light"]

    return build_metric_response(
        value=light_sleep_percent,
        unit="%",
        description=f"Light sleep percent: {light_sleep_percent:.2f}%",
    )


@router.get(
    "/sleep_fragmentation_index",
    response_model=Metric,
    summary="Get sleep fragmentation index",
    description="Calculate sleep fragmentation based on awakenings or awake duration (lower is better)",
)
async def get_sleep_fragmentation_index(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate sleep fragmentation: awakenings / ((deep + light + rem)/3600) or awakeDurationInSeconds"""

    data = extract_sleep_stage_data(sleep_data)

    total_sleep_hours = convert_seconds_to_hours(data.deep + data.light + data.rem)

    if total_sleep_hours == 0:
        raise HTTPException(status_code=404, detail="No sleep time data available")

    if data.awakenings is not None:
        # Use awakenings count if available
        fragmentation = data.awakenings / total_sleep_hours
    else:
        # Use awake duration as fallback
        fragmentation = (
            convert_seconds_to_hours(data.awake_duration)
        ) / total_sleep_hours

    return Metric(
        metric=round(fragmentation, 2),
        unit="index",
        description=f"Sleep fragmentation index: {fragmentation:.2f} (lower is better)",
    )


@router.get(
    "/stage_composition_analysis",
    response_model=Metric,
    summary="Get sleep stage composition analysis",
    description="Get detailed analysis of sleep stage composition vs optimal ranges with overall quality score",
)
async def get_stage_composition_analysis(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Get detailed analysis of sleep stage composition vs optimal ranges"""

    data = extract_sleep_stage_data(sleep_data)
    validate_retrieved_data(data, "sleep_time", "stage composition analysis")

    analysis = analyze_stage_composition(data)

    # Calculate overall sleep quality score
    deep_percent = convert_to_percentage(data.deep, data.sleep_time)
    light_percent = convert_to_percentage(data.light, data.sleep_time)
    rem_percent = convert_to_percentage(data.rem, data.sleep_time)

    # Simple scoring: 100 - sum of deviations from optimal ranges
    deep_score = max(0, 100 - abs(deep_percent - 24.5) * 2)
    light_score = max(0, 100 - abs(light_percent - 47) * 1.5)
    rem_score = max(0, 100 - abs(rem_percent - 26) * 2)

    overall_score = (deep_score + light_score + rem_score) / 3

    return Metric(
        metric=round(overall_score, 2),
        unit="score (0-100)",
        description=f"Overall sleep stage quality: {overall_score:.2f}/100 | {analysis}",
    )


@router.get(
    "/sleep_need_gap_minutes",
    response_model=Metric,
    summary="Get sleep need gap",
    description="Calculate the difference between actual sleep and baseline sleep need in minutes",
)
async def get_sleep_need_gap_minutes(
    sleep_data: dict = Depends(get_garmin_data_dependency("sleep")),
) -> Metric:
    """Calculate sleep need gap minutes: sleepNeed.actual - sleepNeed.baseline"""

    data = extract_sleep_stage_data(sleep_data)
    sleep_need = data.sleep_need

    if not sleep_need:
        raise HTTPException(status_code=404, detail="No sleep need data available")

    gap_minutes = sleep_need.get("actual", 0) - sleep_need.get("baseline", 0)

    return Metric(
        metric=round(gap_minutes, 2),
        unit="minutes",
        description=f"Sleep need gap: {gap_minutes:.2f} minutes (positive = deficit, negative = surplus)",
    )

# Garmin Insights API

A FastAPI application for accessing some extra Garmin health and fitness insights.

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Set up environment variables:

```bash
export GARMIN_EMAIL="your-email@example.com"
export GARMIN_PASSWORD="your-password"
```

3. Run the application:

```bash
python run.py
```

Or using uvicorn directly:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Root

- `GET /` - API information and available endpoints
- `GET /health` - Health check

### Activity Insights

- `GET /insights/activity/health` - Activity API health check
- `GET /insights/activity/step_goal_percent` - Step goal percentage
- `GET /insights/activity/calories_per_step` - Calories per step
- `GET /insights/activity/calories_per_km` - Calories per kilometer
- `GET /insights/activity/stride_length` - Average stride length
- `GET /insights/activity/sedentary_ratio` - Sedentary minutes ratio
- `GET /insights/activity/steps_per_km` - Steps per kilometer
- `GET /insights/activity/active_minutes_percent` - Active minutes percentage
- `GET /insights/activity/calories_per_active_min` - Calories per active minute

### Sleep Insights

- `GET /insights/sleep/health` - Sleep API health check
- `GET /insights/sleep/time_in_bed` - Time in bed
- `GET /insights/sleep/sleep_efficiency` - Sleep efficiency percentage
- `GET /insights/sleep/awakenings_per_hour` - Awakenings per hour
- `GET /insights/sleep/deep_sleep_percent` - Deep sleep percentage
- `GET /insights/sleep/rem_sleep_percent` - REM sleep percentage
- `GET /insights/sleep/light_sleep_percent` - Light sleep percentage
- `GET /insights/sleep/sleep_fragmentation_index` - Sleep fragmentation index
- `GET /insights/sleep/stage_composition_analysis` - Sleep stage composition analysis
- `GET /insights/sleep/sleep_need_gap_minutes` - Sleep need gap in minutes

### Coming Soon

The following modules are planned but not yet implemented:

- **Body Battery Insights** - Body battery level tracking
- **Stress Insights** - Stress level monitoring
- **Respiration Insights** - Respiration rate analysis

## API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

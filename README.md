# 🏃‍♂️ Garmin Insights API

A FastAPI application that provides additional health and fitness insights from your Garmin Connect data. Calculate useful metrics and analytics from your Garmin activity and sleep data.

## ✨ Features

- **📊 Activity Analytics** - Calculate additional metrics from your daily activity data
- **😴 Sleep Analysis** - Analyze sleep quality and patterns
- **⚡ Caching** - Built-in caching for better performance
- **🔒 Authentication** - Uses Garmin's official authentication
- **📚 API Documentation** - Interactive API documentation
- **🎯 Modular** - Easy to add new insight modules

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Poetry (for dependency management)
- Garmin Connect account

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd garmin-insights
   ```

2. **Install dependencies**

   ```bash
   poetry install
   ```

3. **Set up environment variables**

   ```bash
   export GARMIN_EMAIL="your-email@example.com"
   export GARMIN_PASSWORD="your-password"
   ```

   Or create a `.env` file:

   ```bash
   GARMIN_EMAIL=your-email@example.com
   GARMIN_PASSWORD=your-password
   ```

4. **Run the application**

   ```bash
   poetry run python run.py
   ```

   Or with uvicorn directly:

   ```bash
   poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📖 API Reference

### Core Endpoints

| Method | Endpoint  | Description                             |
| ------ | --------- | --------------------------------------- |
| `GET`  | `/`       | API information and available endpoints |
| `GET`  | `/health` | Health check endpoint                   |

### 🏃‍♂️ Activity Insights

Calculate additional metrics from your daily activity data:

| Endpoint                                         | Description                       | Example Response                   |
| ------------------------------------------------ | --------------------------------- | ---------------------------------- |
| `GET /insights/activity/health`                  | Activity API health check         | `{"status": "healthy"}`            |
| `GET /insights/activity/step_goal_percent`       | Step goal completion percentage   | `{"step_goal_percent": 85.2}`      |
| `GET /insights/activity/calories_per_step`       | Average calories burned per step  | `{"calories_per_step": 0.04}`      |
| `GET /insights/activity/calories_per_km`         | Calories burned per kilometer     | `{"calories_per_km": 65.3}`        |
| `GET /insights/activity/stride_length`           | Average stride length in meters   | `{"stride_length": 0.72}`          |
| `GET /insights/activity/sedentary_ratio`         | Ratio of sedentary vs active time | `{"sedentary_ratio": 0.65}`        |
| `GET /insights/activity/steps_per_km`            | Steps taken per kilometer         | `{"steps_per_km": 1389}`           |
| `GET /insights/activity/active_minutes_percent`  | Percentage of active minutes      | `{"active_minutes_percent": 12.5}` |
| `GET /insights/activity/calories_per_active_min` | Calories per active minute        | `{"calories_per_active_min": 8.2}` |

### 😴 Sleep Insights

Calculate sleep quality metrics and patterns:

| Endpoint                                         | Description                         | Example Response                |
| ------------------------------------------------ | ----------------------------------- | ------------------------------- |
| `GET /insights/sleep/health`                     | Sleep API health check              | `{"status": "healthy"}`         |
| `GET /insights/sleep/time_in_bed`                | Total time spent in bed             | `{"time_in_bed_minutes": 480}`  |
| `GET /insights/sleep/sleep_efficiency`           | Sleep efficiency percentage         | `{"sleep_efficiency": 87.5}`    |
| `GET /insights/sleep/awakenings_per_hour`        | Average awakenings per hour         | `{"awakenings_per_hour": 1.2}`  |
| `GET /insights/sleep/deep_sleep_percent`         | Deep sleep percentage               | `{"deep_sleep_percent": 18.3}`  |
| `GET /insights/sleep/rem_sleep_percent`          | REM sleep percentage                | `{"rem_sleep_percent": 22.1}`   |
| `GET /insights/sleep/light_sleep_percent`        | Light sleep percentage              | `{"light_sleep_percent": 59.6}` |
| `GET /insights/sleep/sleep_fragmentation_index`  | Sleep fragmentation score           | `{"fragmentation_index": 15.2}` |
| `GET /insights/sleep/stage_composition_analysis` | Detailed sleep stage analysis       | `{"analysis": {...}}`           |
| `GET /insights/sleep/sleep_need_gap_minutes`     | Gap between actual and needed sleep | `{"sleep_need_gap": -30}`       |

## 🔧 Usage Examples

### Using curl

```bash
# Get step goal percentage
curl http://localhost:8000/insights/activity/step_goal_percent

# Get sleep efficiency
curl http://localhost:8000/insights/sleep/sleep_efficiency

# Get API health
curl http://localhost:8000/health
```

### Using Python requests

```python
import requests

# Get activity insights
response = requests.get("http://localhost:8000/insights/activity/step_goal_percent")
data = response.json()
print(f"Step goal completion: {data['step_goal_percent']}%")

# Get sleep insights
response = requests.get("http://localhost:8000/insights/sleep/sleep_efficiency")
data = response.json()
print(f"Sleep efficiency: {data['sleep_efficiency']}%")
```

### Using JavaScript fetch

```javascript
// Get activity data
fetch("http://localhost:8000/insights/activity/calories_per_step")
  .then((response) => response.json())
  .then((data) => console.log(`Calories per step: ${data.calories_per_step}`));

// Get sleep data
fetch("http://localhost:8000/insights/sleep/deep_sleep_percent")
  .then((response) => response.json())
  .then((data) => console.log(`Deep sleep: ${data.deep_sleep_percent}%`));
```

## 🏗️ Architecture

```
src/
├── main.py                 # FastAPI application entry point
├── garmin_stats/          # Garmin data client with caching
│   └── __init__.py        # GarminStats class
└── api/
    └── insights/          # Insight calculation modules
        ├── activity.py    # Activity-related insights
        └── sleep.py       # Sleep-related insights
```

## 🔮 Roadmap

### Planned Features

- **🔋 Body Battery Insights** - Energy level tracking
- **😰 Stress Insights** - Stress level monitoring
- **🫁 Respiration Insights** - Breathing rate analysis
- **💓 Heart Rate Variability** - HRV trends and recovery metrics

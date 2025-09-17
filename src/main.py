from fastapi import FastAPI
from .api.insights import activity, sleep

app = FastAPI(
    title="Garmin Insights API",
    description="API for accessing some extra Garmin health and fitness insights",
    version="0.1.0"
)

# Include all insight routers
app.include_router(activity.router)
app.include_router(sleep.router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Garmin Insights API",
        "version": "0.1.0",
        "endpoints": {
            "activity": "/insights/activity/",
            "body_battery": "/insights/body-battery/",
            "sleep": "/insights/sleep/",
            "stress": "/insights/stress/",
            "respiration": "/insights/respiration/"
        },
        "sleep_endpoints": {
            "time_in_bed": "/insights/sleep/time_in_bed",
            "sleep_efficiency": "/insights/sleep/sleep_efficiency",
            "awakenings_per_hour": "/insights/sleep/awakenings_per_hour",
            "deep_sleep_percent": "/insights/sleep/deep_sleep_percent",
            "rem_sleep_percent": "/insights/sleep/rem_sleep_percent",
            "light_sleep_percent": "/insights/sleep/light_sleep_percent",
            "sleep_fragmentation_index": "/insights/sleep/sleep_fragmentation_index",
            "stage_composition_analysis": "/insights/sleep/stage_composition_analysis",
            "sleep_need_gap_minutes": "/insights/sleep/sleep_need_gap_minutes",
            "health": "/insights/sleep/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
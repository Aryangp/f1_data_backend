"""F1 Race Telemetry API endpoints"""
from fastapi import APIRouter, HTTPException
import fastf1

from app.schemas.f1 import RaceTelemetryRequest, RaceTelemetryResponse
from app.services.f1_telemetry import (
    enable_cache,
    load_race_session,
    get_race_telemetry
)

router = APIRouter()

# Enable cache on module import
enable_cache()


@router.post("/race-telemetry", response_model=RaceTelemetryResponse)
async def get_race_telemetry_endpoint(request: RaceTelemetryRequest):
    """
    Get race telemetry data for a specific F1 race.
    
    This endpoint loads F1 race session data and processes telemetry for all drivers,
    returning frame-by-frame position, speed, gear, DRS, and other telemetry data.
    
    Args:
        request: Race telemetry request with year, round_number, and refresh_data flag
    
    Returns:
        Race telemetry data including frames, driver colors, and track statuses
    """
    try:
        # Load the race session
        session = load_race_session(request.year, request.round_number)
        
        # Get race telemetry
        telemetry_data = get_race_telemetry(
            session,
            refresh_data=request.refresh_data
        )
        
        return RaceTelemetryResponse(**telemetry_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing race telemetry: {str(e)}"
        )


@router.get("/race-telemetry/{year}/{round_number}")
async def get_race_telemetry_get(
    year: int,
    round_number: int,
    refresh_data: bool = False
):
    """
    Get race telemetry data using GET method (alternative to POST).
    
    Args:
        year: F1 season year (2018-2024)
        round_number: Race round number (1-24)
        refresh_data: Force recomputation of cached data
    
    Returns:
        Race telemetry data
    """
    if year < 2018 or year > 2024:
        raise HTTPException(
            status_code=400,
            detail="Year must be between 2018 and 2024"
        )
    
    if round_number < 1 or round_number > 24:
        raise HTTPException(
            status_code=400,
            detail="Round number must be between 1 and 24"
        )
    
    try:
        session = load_race_session(year, round_number)
        telemetry_data = get_race_telemetry(
            session,
            refresh_data=refresh_data
        )
        
        return RaceTelemetryResponse(**telemetry_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing race telemetry: {str(e)}"
        )


@router.get("/sessions/{year}")
async def get_available_sessions(year: int):
    """
    Get available F1 sessions for a given year.
    
    Args:
        year: F1 season year
    
    Returns:
        List of available sessions
    """
    if year < 2018 or year > 2024:
        raise HTTPException(
            status_code=400,
            detail="Year must be between 2018 and 2024"
        )
    
    try:
        schedule = fastf1.get_event_schedule(year)
        return {
            "year": year,
            "events": schedule.to_dict('records') if not schedule.empty else []
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching schedule: {str(e)}"
        )


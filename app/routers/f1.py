"""F1 Race Telemetry API endpoints"""
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
import fastf1
import orjson
import gzip

from app.schemas.f1 import RaceTelemetryRequest, RaceTelemetryResponse
from app.services.f1_telemetry import (
    enable_cache,
    load_race_session,
    get_race_telemetry
)
from app.services.f1_telemetry_processor import process_and_save_telemetry
from app.services.mongo_logger import mongo_logger

router = APIRouter()

# Enable cache on module import
enable_cache()


@router.post("/race-telemetry")
async def get_race_telemetry_endpoint(
    request: RaceTelemetryRequest,
    compress: bool = Query(True, description="Compress response with gzip")
):
    """
    Get race telemetry data for a specific F1 race.
    
    This endpoint loads F1 race session data and processes telemetry for all drivers,
    returning frame-by-frame position, speed, gear, DRS, and other telemetry data.
    
    Args:
        request: Race telemetry request with year, round_number, refresh_data, and frame_skip
        compress: Whether to compress the response with gzip
    
    Returns:
        Race telemetry data including frames, driver colors, and track statuses
    """
    try:
        # Load the race session
        session = load_race_session(request.year, request.round_number)
        mongo_logger.info(f"Loaded race session for {request.year} Round {request.round_number}")
        
        # Get race telemetry
        telemetry_data = get_race_telemetry(
            session,
            refresh_data=request.refresh_data,
            frame_skip=request.frame_skip
        )
        
        # Serialize with orjson (faster and more compact)
        json_bytes = orjson.dumps(telemetry_data, option=orjson.OPT_SERIALIZE_NUMPY)
        
        if compress:
            # Compress with gzip
            compressed = gzip.compress(json_bytes, compresslevel=6)
            return Response(
                content=compressed,
                media_type="application/json",
                headers={"Content-Encoding": "gzip"}
            )
        else:
            return Response(
                content=json_bytes,
                media_type="application/json"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing race telemetry: {str(e)}"
        )


@router.get("/race-telemetry/{year}/{round_number}")
async def get_race_telemetry_get(
    year: int,
    round_number: int,
    refresh_data: bool = Query(False, description="Force recomputation of cached data"),
    frame_skip: int = Query(1, description="Only include every Nth frame (1=all, 2=every other, etc.)", ge=1, le=10),
    compress: bool = Query(True, description="Compress response with gzip")
):
    """
    Get race telemetry data using GET method (alternative to POST).
    
    Args:
        year: F1 season year (2018-2024)
        round_number: Race round number (1-24)
        refresh_data: Force recomputation of cached data
        frame_skip: Only include every Nth frame (1=all, 2=every other, etc.)
        compress: Whether to compress the response with gzip
    
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
            refresh_data=refresh_data,
            frame_skip=frame_skip
        )
        
        # Serialize with orjson (faster and more compact)
        json_bytes = orjson.dumps(telemetry_data, option=orjson.OPT_SERIALIZE_NUMPY)
        
        if compress:
            # Compress with gzip
            compressed = gzip.compress(json_bytes, compresslevel=6)
            return Response(
                content=compressed,
                media_type="application/json",
                headers={"Content-Encoding": "gzip"}
            )
        else:
            return Response(
                content=json_bytes,
                media_type="application/json"
            )
    
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
        mongo_logger.error(f"Error fetching schedule for {year}: {str(e)}", error=e)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching schedule: {str(e)}"
        )


@router.websocket("/process-telemetry/{year}/{round_number}")
async def websocket_process_telemetry(websocket: WebSocket, year: int, round_number: int):
    """
    WebSocket endpoint to process and save F1 telemetry data with real-time progress updates.
    
    Connect to: ws://localhost:8000/f1/process-telemetry/{year}/{round_number}?frame_skip=1
    
    Args:
        websocket: WebSocket connection
        year: F1 season year (2018-2024)
        round_number: Race round number (1-24)
    
    Query Parameters:
        frame_skip: Frame skipping parameter (default: 1)
    
    Messages sent:
        - Progress updates: {"type": "progress", "message": "...", "progress": 0.0-100.0}
        - Completion: {"type": "complete", "data": {...}}
        - Error: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    mongo_logger.info(f"WebSocket connected for {year} Round {round_number}")
    
    # Get query parameters
    frame_skip = int(websocket.query_params.get("frame_skip", "1"))
    
    # Validate inputs
    if year < 2018 or year > 2024:
        await websocket.send_json({
            "type": "error",
            "message": "Year must be between 2018 and 2024"
        })
        await websocket.close()
        return
    
    if round_number < 1 or round_number > 24:
        await websocket.send_json({
            "type": "error",
            "message": "Round number must be between 1 and 24"
        })
        await websocket.close()
        return
    
    if frame_skip < 1 or frame_skip > 10:
        await websocket.send_json({
            "type": "error",
            "message": "frame_skip must be between 1 and 10"
        })
        await websocket.close()
        return
    
    # Progress callback function
    async def send_progress(message: str, progress: float):
        """Send progress update through WebSocket"""
        try:
            await websocket.send_json({
                "type": "progress",
                "message": message,
                "progress": progress
            })
        except Exception as e:
            print(f"Error sending progress: {e}")
    
    try:
        # Process telemetry in background
        result = await process_and_save_telemetry(
            year=year,
            round_number=round_number,
            progress_callback=send_progress,
            frame_skip=frame_skip
        )
        
        # Send completion message
        if result["success"]:
            await websocket.send_json({
                "type": "complete",
                "data": result
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": result.get("message", "Unknown error"),
                "error": result.get("error")
            })
        
        # Close connection after completion
        await websocket.close()
        mongo_logger.info(f"WebSocket processing completed for {year} Round {round_number}", context=result)
        
    except WebSocketDisconnect:
        mongo_logger.warning(f"WebSocket disconnected for {year} Round {round_number}")
        print("WebSocket disconnected")
    except Exception as e:
        mongo_logger.error(f"WebSocket processing error for {year} Round {round_number}: {str(e)}", error=e)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Processing failed: {str(e)}"
            })
            await websocket.close()
        except:
            pass


@router.post("/process-telemetry")
async def process_telemetry_endpoint(
    year: int = Query(..., description="F1 season year", ge=2018, le=2024),
    round_number: int = Query(..., description="Race round number", ge=1, le=24),
    frame_skip: int = Query(1, description="Frame skipping parameter", ge=1, le=10)
):
    """
    Process and save F1 telemetry data (non-WebSocket version).
    Returns immediately with a task ID. Use WebSocket endpoint for real-time updates.
    
    Args:
        year: F1 season year
        round_number: Race round number
        frame_skip: Frame skipping parameter
    
    Returns:
        Task information
    """
    # Start processing in background
    result = await process_and_save_telemetry(
        year=year,
        round_number=round_number,
        progress_callback=None,  # No progress updates for REST endpoint
        frame_skip=frame_skip
    )
    
    if result["success"]:
        return {
            "status": "completed",
            "data": result
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Processing failed")
        )


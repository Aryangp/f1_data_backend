"""F1 Telemetry Processing Service with Progress Updates"""
import asyncio
from typing import Callable, Optional, Awaitable
from app.services.f1_telemetry import (
    enable_cache,
    load_race_session,
    get_race_telemetry
)
from app.services.mongo_logger import mongo_logger


async def process_and_save_telemetry(
    year: int,
    round_number: int,
    progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None,
    frame_skip: int = 1
) -> dict:
    """
    Process and save F1 race telemetry data with progress updates.
    
    Args:
        year: F1 season year
        round_number: Race round number
        progress_callback: Callback function(status_message, progress_percentage)
        frame_skip: Frame skipping parameter
    
    Returns:
        Dictionary with processing result
    """
    try:
        # Send initial progress
        if progress_callback:
            await progress_callback("Initializing...", 0.0)
        
        mongo_logger.info(f"Starting telemetry processing logic for {year} Round {round_number}")
        
        # Load the race session
        if progress_callback:
            await progress_callback(f"Loading race session for {year} Round {round_number}...", 10.0)
        
        # Run synchronous load_race_session in thread pool
        session = await asyncio.to_thread(load_race_session, year, round_number)
        
        if progress_callback:
            await progress_callback("Processing telemetry data...", 30.0)
        
        # Process telemetry (this will save to file automatically)
        # Force refresh to ensure we process and save
        # Run synchronous get_race_telemetry in thread pool
        telemetry_data = await asyncio.to_thread(
            get_race_telemetry,
            session,
            True,  # refresh_data
            "computed_data",  # cache_dir
            frame_skip
        )
        
        if progress_callback:
            await progress_callback("Finalizing...", 90.0)
        
        # Get event name for file path
        event_name = str(session).replace(' ', '_')
        cache_file = f"computed_data/{event_name}_race_telemetry.json"
        
        result = {
            "success": True,
            "year": year,
            "round_number": round_number,
            "event_name": event_name,
            "file_path": cache_file,
            "frames_count": len(telemetry_data.get("frames", [])),
            "drivers_count": len(telemetry_data.get("driver_colors", {})),
            "message": "Telemetry data processed and saved successfully"
        }
        
        if progress_callback:
            await progress_callback("Complete!", 100.0)
            
        mongo_logger.info("Telemetry processing completed successfully", context=result)
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "year": year,
            "round_number": round_number,
            "error": str(e),
            "message": f"Error processing telemetry: {str(e)}"
        }
        
        mongo_logger.error(f"Error in telemetry processor: {str(e)}", error=e, context=error_result)
        
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 0.0)
        
        return error_result


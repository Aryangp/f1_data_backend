"""F1 API schemas"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class RaceTelemetryRequest(BaseModel):
    """Request schema for race telemetry"""
    year: int = Field(..., description="F1 season year", ge=2018, le=2024)
    round_number: int = Field(..., description="Race round number", ge=1, le=24)
    refresh_data: bool = Field(False, description="Force recomputation of cached data")


class DriverFrame(BaseModel):
    """Driver data for a single frame"""
    x: float
    y: float
    dist: float
    lap: int
    rel_dist: float
    tyre: float
    position: int
    speed: float
    gear: int
    drs: int


class Frame(BaseModel):
    """Single frame of race telemetry"""
    t: float
    lap: int
    drivers: Dict[str, DriverFrame]


class TrackStatus(BaseModel):
    """Track status information"""
    status: str
    start_time: float
    end_time: Optional[float] = None


class RaceTelemetryResponse(BaseModel):
    """Response schema for race telemetry"""
    frames: List[Frame]
    driver_colors: Dict[str, List[int]]  # RGB tuple as list
    track_statuses: List[TrackStatus]
    
    class Config:
        json_schema_extra = {
            "example": {
                "frames": [
                    {
                        "t": 0.0,
                        "lap": 1,
                        "drivers": {
                            "VER": {
                                "x": 100.5,
                                "y": 200.3,
                                "dist": 0.0,
                                "lap": 1,
                                "rel_dist": 0.0,
                                "tyre": 1.0,
                                "position": 1,
                                "speed": 250.0,
                                "gear": 7,
                                "drs": 0
                            }
                        }
                    }
                ],
                "driver_colors": {
                    "VER": [255, 0, 0]
                },
                "track_statuses": [
                    {
                        "status": "1",
                        "start_time": 0.0,
                        "end_time": 100.0
                    }
                ]
            }
        }


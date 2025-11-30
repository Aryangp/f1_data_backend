"""Example schemas"""
from pydantic import BaseModel, Field


class ExampleCreate(BaseModel):
    """Schema for creating an example"""
    message: str = Field(..., description="Example message", min_length=1)


class ExampleResponse(BaseModel):
    """Schema for example response"""
    id: int = Field(..., description="Example ID")
    message: str = Field(..., description="Example message")
    status: str = Field(..., description="Status of the operation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "message": "This is an example",
                "status": "success"
            }
        }


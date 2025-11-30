"""Main API endpoints"""
from fastapi import APIRouter, HTTPException
from app.schemas.example import ExampleResponse, ExampleCreate

router = APIRouter()


@router.get("/", response_model=ExampleResponse)
async def get_example():
    """Example GET endpoint"""
    return ExampleResponse(
        id=1,
        message="This is an example response",
        status="success"
    )


@router.post("/example", response_model=ExampleResponse)
async def create_example(data: ExampleCreate):
    """Example POST endpoint"""
    # Add your business logic here
    return ExampleResponse(
        id=2,
        message=f"Created: {data.message}",
        status="success"
    )


@router.get("/example/{item_id}", response_model=ExampleResponse)
async def get_example_by_id(item_id: int):
    """Example GET endpoint with path parameter"""
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Item ID must be positive")
    
    return ExampleResponse(
        id=item_id,
        message=f"Retrieved item {item_id}",
        status="success"
    )


"""GPS router placeholder"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_gps_data():
    return {"message": "GPS data endpoint - TODO: Implementer"}

@router.post("/data")
async def upload_gps_data():
    return {"message": "Upload GPS data endpoint - TODO: Implementer"} 
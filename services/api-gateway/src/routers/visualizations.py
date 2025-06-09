"""Visualizations router placeholder"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_visualization():
    return {"message": "Generate visualization endpoint - TODO: Implementer"}

@router.get("/")
async def list_visualizations():
    return {"message": "List visualizations endpoint - TODO: Implementer"} 
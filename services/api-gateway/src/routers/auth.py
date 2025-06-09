"""Auth router placeholder"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    return {"message": "Login endpoint - TODO: Implementer"}

@router.post("/register")
async def register():
    return {"message": "Register endpoint - TODO: Implementer"} 
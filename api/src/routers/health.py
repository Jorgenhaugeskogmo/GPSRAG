"""
Health check router for GPSRAG API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import time
from typing import Dict, Any

from ..database import get_db
from ..config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basis helse-sjekk"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detaljert helse-sjekk som tester alle avhengigheter"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "services": {}
    }
    
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Test Weaviate connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.weaviate_url}/v1/.well-known/ready", timeout=5.0)
            if response.status_code == 200:
                health_status["services"]["weaviate"] = {"status": "healthy"}
            else:
                health_status["services"]["weaviate"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["weaviate"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Test RAG Engine connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.rag_engine_url}/health", timeout=5.0)
            if response.status_code == 200:
                health_status["services"]["rag_engine"] = {"status": "healthy"}
            else:
                health_status["services"]["rag_engine"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["rag_engine"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status 
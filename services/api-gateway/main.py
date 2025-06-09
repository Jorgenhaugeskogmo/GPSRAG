"""
GPSRAG API Gateway
Hovedapplikasjon som håndterer alle API-kall og koordinerer mellom tjenester
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import List, Optional
import asyncio

from src.config import settings
from src.database import engine, get_db, Base
from src.routers import auth, chat, documents, gps, visualizations, health
from src.services.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket manager
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Applikasjonens livsyklus-handler"""
    # Startup
    logger.info("🚀 Starter GPSRAG API Gateway...")
    
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tabeller initialisert")
    
    # TODO: Initialize vector database schema
    # TODO: Verify external service connections
    
    yield
    
    # Shutdown
    logger.info("🔄 Stopper GPSRAG API Gateway...")

# Create FastAPI app
app = FastAPI(
    title="GPSRAG API",
    description="RAG-drevet GPS Data Chatapplikasjon API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(gps.router, prefix="/gps", tags=["gps"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(visualizations.router, prefix="/visualizations", tags=["visualizations"])

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endepunkt for sanntidskommunikasjon"""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: Behandle WebSocket-meldinger
            await websocket_manager.send_personal_message(f"Echo: {data}", client_id)
    except Exception as e:
        logger.error(f"WebSocket feil: {e}")
    finally:
        await websocket_manager.disconnect(client_id)

@app.get("/")
async def root():
    """Root endepunkt med grunnleggende informasjon"""
    return {
        "message": "Velkommen til GPSRAG API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": True}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
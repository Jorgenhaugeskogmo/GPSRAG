"""
GPSRAG API Gateway
Hovedapplikasjon som håndterer alle API-kall og koordinerer mellom tjenester
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import List, Optional
import asyncio
from pathlib import Path

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
    allow_origins=["*"],  # Åpnet for alle origins for produksjon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(gps.router, prefix="/api/gps", tags=["gps"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(visualizations.router, prefix="/api/visualizations", tags=["visualizations"])

# Serve frontend static files if they exist
frontend_path = Path("../frontend")
if frontend_path.exists():
    # Serve Next.js static files
    app.mount("/_next/static", StaticFiles(directory="../frontend/.next/static"), name="next-static")
    app.mount("/static", StaticFiles(directory="../frontend/public"), name="public")

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

@app.get("/api")
async def api_root():
    """API root endepunkt"""
    return {
        "message": "Velkommen til GPSRAG API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

# Serve frontend index.html for all non-API routes
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve frontend React app for alle ruter som ikke er API"""
    frontend_index = Path("../frontend/server.js")
    if frontend_index.exists():
        # Hvis Next.js standalone er tilgjengelig
        return FileResponse("../frontend/server.js")
    else:
        # Fallback til API informasjon
        return {
            "message": "Velkommen til GPSRAG API",
            "version": "1.0.0",
            "status": "active",
            "docs": "/docs",
            "frontend": "Frontend integrasjon pågår..."
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
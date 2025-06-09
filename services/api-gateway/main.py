"""
GPSRAG API Gateway
Hovedapplikasjon som håndterer alle API-kall og koordinerer mellom tjenester
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import List, Optional
import asyncio
from pathlib import Path
import httpx

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
frontend_static_path = Path("../frontend/.next/static")
frontend_public_path = Path("../frontend/public")
if frontend_static_path.exists():
    # Serve Next.js static files
    app.mount("/_next/static", StaticFiles(directory="../frontend/.next/static"), name="next-static")
if frontend_public_path.exists():
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

# Proxy frontend requests to Next.js server
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_frontend(request: Request, path: str):
    """Proxy alle ikke-API ruter til Next.js frontend serveren"""
    # Sjekk om dette er en API-rute som ikke skal proxies
    if path.startswith("api/") or path in ["docs", "redoc"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Proxy til Next.js server
    frontend_port = int(os.getenv("PORT", "8000")) + 1
    frontend_url = f"http://localhost:{frontend_port}"
    
    try:
        async with httpx.AsyncClient() as client:
            # Bygg proxy URL
            target_url = f"{frontend_url}/{path}" if path else frontend_url
            
            # Kopier headers fra original request
            headers = dict(request.headers)
            headers.pop("host", None)  # Fjern host header
            
            # Proxy request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body() if request.method in ["POST", "PUT", "PATCH"] else None,
                timeout=30.0
            )
            
            # Return proxied response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    except Exception as e:
        logger.error(f"Frontend proxy feil: {e}")
        # Fallback response
        return {
            "message": "GPSRAG Fullstack App",
            "version": "1.0.0",
            "status": "active",
            "api_docs": "/docs",
            "frontend_error": f"Frontend ikke tilgjengelig: {str(e)}"
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
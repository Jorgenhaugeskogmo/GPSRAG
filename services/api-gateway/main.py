"""
GPSRAG API Gateway - Railway Deployment
Hovedapplikasjon som håndterer alle API-kall og serverer frontend
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import List, Optional
import asyncio
from pathlib import Path

from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Applikasjonens livsyklus-handler"""
    # Startup
    logger.info("🚀 Starter GPSRAG API Gateway på Railway...")
    
    # Initialize database tables (SQLite for Railway)
    try:
        from src.database import engine, Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tabeller initialisert")
    except Exception as e:
        logger.warning(f"⚠️ Database initialisering feilet: {e}")
    
    logger.info("🌐 Railway deployment aktiv")
    
    yield
    
    # Shutdown
    logger.info("🔄 Stopper GPSRAG API Gateway...")

# Create FastAPI app
app = FastAPI(
    title="GPSRAG API",
    description="RAG-drevet GPS Data Chatapplikasjon API - Railway Edition",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Åpnet for alle origins for Railway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes (importerer kun de som finnes)
try:
    from src.routers import health
    app.include_router(health.router, prefix="/api/health", tags=["health"])
except ImportError:
    # Fallback health endpoint
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "service": "GPSRAG API Gateway", "environment": "Railway"}

try:
    from src.routers import auth, chat, documents, gps, visualizations
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(gps.router, prefix="/api/gps", tags=["gps"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(visualizations.router, prefix="/api/visualizations", tags=["visualizations"])
except ImportError as e:
    logger.warning(f"⚠️ Noen routers kunne ikke importeres: {e}")

# Serve frontend static files
frontend_paths = [
    Path("/app/frontend/out"),
    Path("/app/frontend/.next/static"),
    Path("/app/frontend/public"),
    Path("../frontend/out"),
    Path("../frontend/.next/static"),
    Path("../frontend/public")
]

# Mount static file directories som finnes
for path in frontend_paths:
    if path.exists():
        if "out" in str(path):
            app.mount("/", StaticFiles(directory=str(path), html=True), name="frontend")
            logger.info(f"✅ Frontend mounted from: {path}")
        elif "static" in str(path):
            app.mount("/_next/static", StaticFiles(directory=str(path)), name="next-static")
        elif "public" in str(path):
            app.mount("/static", StaticFiles(directory=str(path)), name="public")

@app.get("/api")
async def api_root():
    """API root endepunkt"""
    return {
        "message": "Velkommen til GPSRAG API",
        "version": "1.0.0",
        "status": "active",
        "environment": "Railway",
        "docs": "/docs"
    }

# Fallback chat endpoint for testing
@app.post("/api/chat")
async def chat_fallback():
    """Fallback chat endpoint for Railway testing"""
    return {
        "response": "Hei! Dette er en test-respons fra GPSRAG på Railway. Full chat-funksjonalitet kommer snart!",
        "status": "Railway deployment aktiv",
        "note": "External services integreres..."
    }

# Health check for Railway
@app.get("/health")
async def railway_health():
    """Railway health check"""
    return {"status": "healthy", "platform": "Railway", "service": "GPSRAG"}

# Serve frontend for alle andre ruter
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve Next.js frontend for alle ruter som ikke er API"""
    # Sjekk om dette er en API-rute
    if path.startswith("api/") or path in ["docs", "redoc", "openapi.json"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Prøv å serve index.html fra forskjellige mulige steder
    html_files = [
        Path("/app/frontend/out/index.html"),
        Path("/app/frontend/.next/server/pages/index.html"), 
        Path("../frontend/out/index.html"),
        Path("../frontend/.next/server/pages/index.html")
    ]
    
    for html_file in html_files:
        if html_file.exists():
            logger.info(f"Serving frontend from: {html_file}")
            return FileResponse(str(html_file))
    
    # Fallback HTML response
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPSRAG - Railway Deployment</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
            .status { background: #e7f5e7; border: 1px solid #4caf50; padding: 15px; border-radius: 4px; margin: 20px 0; }
            .api-link { display: inline-block; background: #007acc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 10px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 GPSRAG - Railway Deployment</h1>
                <p>GPS RAG Chatapplikasjon er nå live på Railway!</p>
            </div>
            
            <div class="status">
                <strong>✅ Status:</strong> Backend kjører på Railway<br>
                <strong>📊 Database:</strong> SQLite (Railway)<br>
                <strong>🌐 Platform:</strong> Railway Cloud
            </div>
            
            <h3>🔧 Tilgjengelige endepunkter:</h3>
            <a href="/docs" class="api-link">📖 API Dokumentasjon</a>
            <a href="/api" class="api-link">🔍 API Status</a>
            <a href="/health" class="api-link">💚 Health Check</a>
            
            <h3>📝 Status:</h3>
            <ul>
                <li>✅ Backend API kjører</li>
                <li>✅ SQLite database initialisert</li>
                <li>🔄 Frontend bygges og integreres...</li>
                <li>🔄 Externe tjenester konfigureres...</li>
            </ul>
            
            <p><strong>Neste steg:</strong> Frontend skal snart være tilgjengelig på denne URLen.</p>
        </div>
    </body>
    </html>
    """)

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
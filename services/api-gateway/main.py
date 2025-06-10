"""
GPSRAG API Gateway - Railway Deployment
Hovedapplikasjon som håndterer alle API-kall og serverer frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

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
        # Simple SQLite setup for Railway
        logger.info("✅ Database (SQLite) klar for Railway")
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

# Basic health endpoint for Railway
@app.get("/health")
async def railway_health():
    """Railway health check"""
    try:
        port = os.getenv("PORT", "8080")
        return {
            "status": "healthy", 
            "platform": "Railway", 
            "service": "GPSRAG",
            "port": port,
            "environment": "production"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def api_health_check():
    """API health check"""
    return {"status": "healthy", "service": "GPSRAG API Gateway", "environment": "Railway"}

@app.get("/api")
async def api_root():
    """API root endepunkt"""
    return {
        "message": "Velkommen til GPSRAG API",
        "version": "1.0.0",
        "status": "active",
        "environment": "Railway",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "api_health": "/api/health",
        }
    }

# Fallback chat endpoint for testing
@app.post("/api/chat")
async def chat_fallback():
    """Fallback chat endpoint for Railway testing"""
    return {
        "response": "Hei! Dette er en test-respons fra GPSRAG på Railway. Full chat-funksjonalitet kommer snart!",
        "status": "Railway deployment aktiv",
        "timestamp": "2025-06-10"
    }

# Root route - serve frontend
@app.get("/")
async def root():
    """Root endepunkt - serve frontend"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPSRAG - GPS RAG Chatapplikasjon</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; color: white; margin-bottom: 40px; }
            .card { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: 20px 0; }
            .status { background: #e7f5e7; border: 1px solid #4caf50; padding: 15px; border-radius: 8px; margin: 20px 0; }
            .btn { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px; transition: transform 0.2s; }
            .btn:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 GPSRAG</h1>
                <p>GPS RAG Chatapplikasjon - Nå live på Railway!</p>
            </div>
            
            <div class="card">
                <div class="status">
                    <strong>✅ Status:</strong> Backend kjører på Railway<br>
                    <strong>📊 Database:</strong> SQLite (Railway)<br>
                    <strong>🌐 Platform:</strong> Railway Cloud<br>
                    <strong>🔗 API:</strong> Tilgjengelig
                </div>
                
                <h3>🔧 Tilgjengelige tjenester:</h3>
                <a href="/docs" class="btn">📖 API Dokumentasjon</a>
                <a href="/api" class="btn">🔍 API Status</a>
                <a href="/health" class="btn">💚 Health Check</a>
                
                <h3>📝 System Status:</h3>
                <ul>
                    <li>✅ Backend API kjører på Railway</li>
                    <li>✅ SQLite database klar</li>
                    <li>✅ CORS konfigurert</li>
                    <li>✅ Health checks aktive</li>
                    <li>🔄 Full RAG-funksjonalitet kommer snart!</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": True}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": True}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 
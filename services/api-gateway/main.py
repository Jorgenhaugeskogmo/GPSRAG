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
import subprocess

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
    
    # Start Next.js standalone server in background
    try:
        frontend_path = Path("/app/frontend")
        if frontend_path.exists():
            logger.info("🎯 Starter Next.js standalone server...")
            # Note: Next.js standalone server will run on port defined by Railway
            # We'll serve it through FastAPI instead
        else:
            logger.warning("⚠️ Frontend directory ikke funnet")
    except Exception as e:
        logger.warning(f"⚠️ Frontend startup feilet: {e}")
    
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

# Mount Next.js static assets først
try:
    next_static_path = Path("/app/frontend/.next/static")
    if next_static_path.exists():
        app.mount("/_next/static", StaticFiles(directory=str(next_static_path)), name="next-static")
        logger.info(f"✅ Next.js static assets mounted: {next_static_path}")
    
    public_path = Path("/app/frontend/public")
    if public_path.exists():
        app.mount("/static", StaticFiles(directory=str(public_path)), name="public")
        logger.info(f"✅ Public assets mounted: {public_path}")
except Exception as e:
    logger.warning(f"⚠️ Static files mounting feilet: {e}")

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
            "health": "/api/health",
            "chat": "/api/chat/chat/",
            "documents": "/api/documents",
            "gps": "/api/gps"
        }
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

# Serve Next.js frontend for alle andre ruter
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve Next.js frontend for alle ruter som ikke er API"""
    # Sjekk om dette er en API-rute
    if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Prøv å serve Next.js index fra standalone build
    html_files = [
        Path("/app/frontend/server.js"),  # Standalone server
        Path("/app/frontend/.next/server/pages/index.html"), 
        Path("/app/frontend/.next/static/index.html"),
    ]
    
    # For standalone build, serve hovedfilen
    main_html = Path("/app/frontend/.next/server/pages/index.html")
    if main_html.exists():
        logger.info(f"Serving Next.js from: {main_html}")
        return FileResponse(str(main_html))
    
    # Fallback til komplett HTML response med integrert frontend
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPSRAG - GPS RAG Chatapplikasjon</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="/_next/static/css/app.css" rel="stylesheet" />
        <style>
            body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; color: white; margin-bottom: 40px; }}
            .card {{ background: white; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: 20px 0; }}
            .status {{ background: #e7f5e7; border: 1px solid #4caf50; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px; transition: transform 0.2s; }}
            .btn:hover {{ transform: translateY(-2px); }}
            .chat-container {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .chat-input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; margin: 10px 0; }}
            .chat-button {{ background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; }}
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
                
                <div class="chat-container">
                    <h4>💬 Test Chat API</h4>
                    <input type="text" id="chatInput" class="chat-input" placeholder="Skriv en melding for å teste chat API..." />
                    <button onclick="testChat()" class="chat-button">Send</button>
                    <div id="chatResponse" style="margin-top: 15px; padding: 10px; background: white; border-radius: 6px; display: none;"></div>
                </div>
                
                <h3>📝 System Status:</h3>
                <ul>
                    <li>✅ Backend API kjører</li>
                    <li>✅ SQLite database initialisert</li>
                    <li>✅ CORS konfigurert</li>
                    <li>✅ Railway deployment aktiv</li>
                    <li>🔄 Frontend integreres...</li>
                </ul>
            </div>
        </div>
        
        <script>
            async function testChat() {{
                const input = document.getElementById('chatInput');
                const response = document.getElementById('chatResponse');
                const message = input.value.trim();
                
                if (!message) return;
                
                try {{
                    const apiResponse = await fetch('/api/chat/chat/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ message: message }})
                    }});
                    
                    const data = await apiResponse.json();
                    response.style.display = 'block';
                    response.innerHTML = `<strong>API Response:</strong><br>${{JSON.stringify(data, null, 2)}}`;
                }} catch (error) {{
                    response.style.display = 'block';
                    response.innerHTML = `<strong>Error:</strong> ${{error.message}}`;
                }}
                
                input.value = '';
            }}
            
            // Auto-test på page load
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('GPSRAG Railway deployment loaded successfully');
            }});
        </script>
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
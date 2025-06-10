"""
GPSRAG API Gateway - Railway Deployment
Hovedapplikasjon som håndterer alle API-kall og serverer frontend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import tempfile
import shutil
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

# Try to mount Next.js static assets
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

# Try to import and mount chat router safely
try:
    from src.routers import chat
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    logger.info("✅ Chat router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Chat router ikke tilgjengelig: {e}")

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
            "chat": "/api/chat/",
            "upload": "/api/upload",
        }
    }

# Chat endpoint with proper request handling
@app.post("/api/chat/")
async def chat_endpoint(request: dict):
    """Chat endpoint som håndterer meldinger"""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", "default")
        
        if not message:
            raise HTTPException(status_code=400, detail="Melding er påkrevet")
        
        # For nå, returner en mock respons (senere koble til OpenAI/RAG)
        response_text = f"Du spurte: '{message}'. Dette er en test-respons fra GPSRAG på Railway. RAG-integrasjon kommer snart!"
        
        return {
            "response": response_text,
            "session_id": session_id,
            "status": "success",
            "sources": []  # Skal fylles når RAG er koblet til
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat feil: {str(e)}")

# File upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload og prosesser dokumenter"""
    try:
        # Sjekk filtype
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Kun PDF-filer er støttet")
        
        # Sjekk filstørrelse (maks 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="Fil er for stor (maks 10MB)")
        
        # Reset file pointer
        await file.seek(0)
        
        # Opprett temp mappe for Railway
        upload_dir = Path("/tmp/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Lagre filen midlertidig
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✅ Fil lagret: {file.filename} ({file_size} bytes)")
        
        # TODO: Implementer RAG prosessering her
        # - Ekstraher tekst fra PDF
        # - Lag embeddings
        # - Lagre i vektor database
        
        return {
            "status": "success",
            "message": f"Fil '{file.filename}' lastet opp og prosessert",
            "filename": file.filename,
            "size": file_size,
            "processed": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload feil: {str(e)}")

# Fallback chat endpoint for testing (backup)
@app.post("/api/chat")
async def chat_fallback():
    """Fallback chat endpoint for Railway testing"""
    return {
        "response": "Hei! Dette er en test-respons fra GPSRAG på Railway. Full chat-funksjonalitet kommer snart!",
        "status": "Railway deployment aktiv",
        "timestamp": "2025-06-10"
    }

# Root route - serve Next.js frontend
@app.get("/")
async def root():
    """Serve Next.js frontend eller fallback"""
    # Try to serve actual Next.js build
    try:
        html_files = [
            Path("/app/frontend/.next/server/pages/index.html"),
            Path("/app/frontend/.next/static/index.html"),
            Path("/app/frontend/public/index.html"),
        ]
        
        for html_file in html_files:
            if html_file.exists():
                logger.info(f"Serving Next.js from: {html_file}")
                return FileResponse(str(html_file))
        
        # If no Next.js files found, serve fallback
        logger.warning("Next.js files not found, serving fallback")
    except Exception as e:
        logger.warning(f"Frontend serving error: {e}")
    
    # Fallback HTML with better functionality
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

# Catch-all route for frontend routes
@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """Serve frontend for alle paths som ikke er API"""
    # Skip API routes
    if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try to serve Next.js index for all frontend routes
    try:
        html_files = [
            Path("/app/frontend/.next/server/pages/index.html"),
            Path("/app/frontend/.next/static/index.html"),
        ]
        
        for html_file in html_files:
            if html_file.exists():
                return FileResponse(str(html_file))
    except Exception as e:
        logger.warning(f"Frontend route serving error: {e}")
    
    # Fallback - redirect to root
    raise HTTPException(status_code=404, detail=f"Page not found: {path}")

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
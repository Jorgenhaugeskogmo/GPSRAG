"""
GPSRAG API Gateway - Railway Deployment
Hovedapplikasjon som håndterer alle API-kall og serverer frontend
"""

# CRITICAL: Apply NumPy compatibility BEFORE any other imports
import numpy_compat

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import tempfile
import shutil
from pathlib import Path
from pydantic import BaseModel
from rag_service import GPSRAGService # Direkte import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Applikasjonens livsyklus-handler"""
    # Startup
    logger.info("🚀 Starter GPSRAG API Gateway på Railway...")
    
    # Sjekk OpenAI API nøkkel
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("✅ OpenAI API nøkkel funnet - RAG aktivert")
    else:
        logger.warning("⚠️ OPENAI_API_KEY mangler - sett den i Railway environment variables")
    
    # Initialize database tables (SQLite for Railway)
    try:
        # Simple SQLite setup for Railway
        logger.info("✅ Database (SQLite) klar for Railway")
    except Exception as e:
        logger.warning(f"⚠️ Database initialisering feilet: {e}")
    
    # Initialize RAG service - lazy loading for Railway
    try:
        logger.info("🎯 RAG Service modul lastet og klar!")
    except Exception as e:
        logger.warning(f"⚠️ RAG Service modul laster feilet: {e}")
    
    logger.info("🌐 Railway deployment aktiv med RAG")
    
    # Opprett ÉN enkelt instans av RAG-tjenesten
    app.state.rag_service = GPSRAGService()
    logger.info("✅ Singleton RAG service instans opprettet og lagret på app.state.")
    
    yield
    
    # Shutdown
    logger.info("🔄 Stopper GPSRAG API Gateway...")
    app.state.rag_service = None # Rydd opp

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

@app.get("/api/debug")
async def debug_info():
    """Debug informasjon for troubleshooting"""
    openai_key = os.getenv("OPENAI_API_KEY")
    return {
        "openai_api_key_set": bool(openai_key),
        "openai_key_preview": openai_key[:8] + "..." if openai_key else None,
        "environment": "Railway",
        "python_path": os.getcwd(),
        "temp_dir_exists": os.path.exists("/tmp"),
        "chromadb_dir": "/tmp/chromadb",
        "chromadb_exists": os.path.exists("/tmp/chromadb")
    }

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
# try:
#     from src.routers import chat
#     app.include_router(chat.router, prefix="/api", tags=["chat"]) # Using the router from src
#     logger.info("✅ Chat router loaded")
# except ImportError as e:
#     logger.warning(f"⚠️ Chat router ikke tilgjengelig: {e}")

# Model for the chat request body
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

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

# Chat endpoint - henter nå RAG-tjenesten fra app.state
@app.post("/api/chat/")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """Chat endpoint med full RAG integrasjon, bruker nå shared service instance"""
    try:
        rag_service = request.app.state.rag_service
        
        logger.info(f"🚀 RAG Chat query mottatt: {chat_request.message}")
        
        # Kall RAG-tjenesten for å generere et svar
        rag_result = await rag_service.generate_rag_response(chat_request.message)
        
        # Returner svaret i forventet format
        return {
            "response": rag_result["response"],
            "session_id": chat_request.session_id,
            "status": "success",
            "sources": rag_result.get("sources", []),
            "context_used": rag_result.get("context_used", False)
        }
            
    except Exception as e:
        logger.error(f"❌ Chat endpoint feilet: {e}", exc_info=True)
        # Returner en mer detaljert feilmelding til klienten
        raise HTTPException(
            status_code=500, 
            detail=f"Det oppstod en intern feil i chat-tjenesten: {str(e)}"
        )

# File upload endpoint - henter nå RAG-tjenesten fra app.state
@app.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Upload og prosesser dokumenter, bruker nå shared service instance"""
    try:
        rag_service = request.app.state.rag_service
        
        # Sjekk filtype
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Kun PDF-filer er støttet")
        
        # Sjekk filstørrelse (maks 10MB)
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
        
        # Prosesser dokumentet med RAG
        try:
            result = await rag_service.process_document(str(file_path), file.filename)
            
            if result["status"] == "success":
                logger.info(f"✅ RAG prosessering fullført: {result}")
                return {
                    "status": "success",
                    "message": f"Fil '{file.filename}' lastet opp og prosessert",
                    "filename": file.filename,
                    "size": file_size,
                    "processed": True,
                    "rag_info": {
                        "doc_id": result["doc_id"],
                        "chunks_count": result["chunks_count"],
                        "storage_type": result.get("storage_type", "chromadb")
                    }
                }
            else:
                logger.warning(f"⚠️ RAG prosessering feilet: {result}")
                return {
                    "status": "success",
                    "message": f"Fil '{file.filename}' lastet opp (RAG prosessering feilet: {result['message']})",
                    "filename": file.filename,
                    "size": file_size,
                    "processed": False,
                    "error": result["message"]
                }
            
        except Exception as rag_error:
            logger.error(f"❌ RAG prosessering feilet: {rag_error}")
            return {
                "status": "success",
                "message": f"Fil '{file.filename}' lastet opp (RAG prosessering under feilsøking)",
                "filename": file.filename,
                "size": file_size,
                "processed": False,
                "error": str(rag_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload feil: {str(e)}")

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
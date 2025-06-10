"""
Railway Entry Point for GPSRAG Fullstack
Serverer både API og frontend static files
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# Import API endpoints
from chat import app as chat_app
from upload import app as upload_app

# Lag hovedapplikasjonen
app = FastAPI(title="GPSRAG Fullstack", description="GPS RAG System med chat og upload")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints
app.mount("/api/chat", chat_app)
app.mount("/api/upload", upload_app)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "GPSRAG Fullstack"}

# Serve Next.js static files
frontend_path = Path(__file__).parent.parent / "frontend"
if (frontend_path / ".next").exists():
    # Serve Next.js build output
    app.mount("/_next", StaticFiles(directory=str(frontend_path / ".next")), name="nextjs_build")
    
    # Serve public assets
    if (frontend_path / "public").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_path / "public")), name="public_assets")

# Catch-all route for frontend
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve Next.js frontend for all unmatched routes"""
    frontend_path = Path(__file__).parent.parent / "frontend"
    
    # Try to serve specific file first
    if full_path and not full_path.startswith("api/"):
        file_path = frontend_path / ".next" / "server" / "pages" / f"{full_path}.html"
        if file_path.exists():
            return FileResponse(str(file_path))
    
    # Default to index.html for SPA routing
    index_path = frontend_path / ".next" / "server" / "pages" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    # Fallback til enkel HTML hvis Next.js build ikke finnes
    return {"message": "GPSRAG Fullstack - Frontend ikke bygget ennå"}

# Export for Railway
handler = app

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
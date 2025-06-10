"""
Railway Entry Point for GPSRAG Fullstack
Serverer både API og frontend static files
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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

# Serve static files (for ultra-minimal deployment)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve Next.js static files (if available)
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
    """Serve frontend - Next.js hvis tilgjengelig, ellers minimal HTML"""
    
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Check for ultra-minimal static HTML
    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    
    # Try Next.js frontend
    frontend_path = Path(__file__).parent.parent / "frontend"
    if (frontend_path / ".next").exists():
        # Try to serve specific file first
        if full_path and not full_path.startswith("api/"):
            file_path = frontend_path / ".next" / "server" / "pages" / f"{full_path}.html"
            if file_path.exists():
                return FileResponse(str(file_path))
        
        # Default to index.html for SPA routing
        index_path = frontend_path / ".next" / "server" / "pages" / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    
    # Fallback til inline HTML for ultra-minimal deployment
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPSRAG API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            h1 { color: #333; }
            .api-link { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🚀 GPSRAG API er aktiv</h1>
        <p>Backend API kjører og er klar for bruk.</p>
        <p><a href="/docs" class="api-link">📖 API Dokumentasjon</a></p>
        <p><strong>Tilgjengelige endepunkter:</strong></p>
        <ul>
            <li><code>/health</code> - System status</li>
            <li><code>/api/chat/</code> - Chat API</li>
            <li><code>/api/upload/</code> - Upload API</li>
            <li><code>/docs</code> - Interactive API docs</li>
        </ul>
    </body>
    </html>
    """)

# Export for Railway
handler = app

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
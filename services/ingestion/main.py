"""
Ingestion Service - Håndterer dokument-upload og prosessering
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GPSRAG Ingestion Service",
    description="Håndterer dokument-upload og prosessering",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ingestion"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload og prosesser et dokument"""
    try:
        # Placeholder implementasjon
        logger.info(f"Mottatt fil: {file.filename}")
        
        # TODO: Implementer faktisk filprosessering
        return {
            "message": "Fil mottatt og prosessert",
            "filename": file.filename,
            "size": file.size
        }
    except Exception as e:
        logger.error(f"Feil under filopplasting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 
"""
Visualization Service - Håndterer GPS-data visualisering
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GPSRAG Visualization Service",
    description="Håndterer GPS-data visualisering",
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

class VisualizationRequest(BaseModel):
    data_type: str
    parameters: dict = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "visualization"}

@app.post("/generate")
async def generate_visualization(request: VisualizationRequest):
    """Generer en visualisering basert på GPS-data"""
    try:
        logger.info(f"Genererer visualisering for: {request.data_type}")
        
        # TODO: Implementer faktisk visualiseringsgenerering
        sample_data = {
            "chart_type": request.data_type,
            "data": [
                {"x": 1, "y": 10},
                {"x": 2, "y": 20},
                {"x": 3, "y": 15}
            ],
            "config": {
                "title": f"GPS Data Visualisering - {request.data_type}",
                "xAxis": "Tid",
                "yAxis": "Verdi"
            }
        }
        
        return sample_data
    except Exception as e:
        logger.error(f"Feil under visualiseringsgenerering: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 
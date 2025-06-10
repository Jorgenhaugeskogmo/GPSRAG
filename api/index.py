"""
Railway Entry Point for GPSRAG
Importerer og eksponerer FastAPI applikasjonen
"""

# Import the FastAPI app from chat.py
from chat import app

# Export the app for Railway
handler = app

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
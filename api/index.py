"""
Vercel API Entry Point for GPSRAG
Importerer og eksponerer hele API Gateway applikasjonen
"""

import os
import sys
from pathlib import Path

# Add the services directory to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
services_dir = project_root / "services" / "api-gateway"
sys.path.insert(0, str(services_dir))

# Import the FastAPI app from api-gateway
from main import app

# Export the app for Vercel
handler = app 
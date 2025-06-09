"""
Vercel RAG Engine Entry Point for GPSRAG
Importerer og eksponerer RAG engine applikasjonen
"""

import os
import sys
from pathlib import Path

# Add the current api directory to the Python path for rag_src
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add the services directory to the Python path
project_root = current_dir.parent
services_dir = project_root / "services" / "rag-engine"
sys.path.insert(0, str(services_dir))

# Import the FastAPI app from rag-engine
from main import app

# Export the app for Vercel
handler = app 
#!/bin/bash

# Sett PORT fallback
export PORT=${PORT:-8000}

echo "🚀 Starter GPSRAG Fullstack på port $PORT"

# Start backend med fullstack konfiguration
cd /app/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT 
#!/bin/bash

# Sett PORT fallback
export PORT=${PORT:-8000}

echo "🚀 Starter GPSRAG Fullstack på port $PORT"

# Gå til backend mappen og start FastAPI direkte
cd /app/backend
echo "🔧 Starter integrert fullstack applikasjon på port $PORT"

# Start FastAPI som serverer både API og frontend
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT 
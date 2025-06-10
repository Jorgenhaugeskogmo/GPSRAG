#!/bin/bash

# GPSRAG Fullstack Startup for Railway
echo "🚀 Starter GPSRAG på Railway..."

# Sett standardverdier hvis ikke definert
export PORT=${PORT:-8000}
export NODE_ENV=${NODE_ENV:-production}

# Logg miljøvariabler (uten å eksponere hemmeligheter)
echo "📋 Miljø:"
echo "  PORT: $PORT"
echo "  NODE_ENV: $NODE_ENV"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:+***set***}"
echo "  WEAVIATE_URL: ${WEAVIATE_URL:-not set}"

# Start frontend i bakgrunnen
echo "🎨 Starter Next.js frontend..."
cd /app/frontend
npm start &
FRONTEND_PID=$!

# Vent litt for frontend å starte
sleep 3

# Start backend API
echo "🔧 Starter FastAPI backend..."
cd /app/backend
python -m uvicorn index:app --host 0.0.0.0 --port $PORT &
BACKEND_PID=$!

# Health check function
health_check() {
    curl -f http://localhost:$PORT/health > /dev/null 2>&1
    return $?
}

# Vent på at backend er klar
echo "⏳ Venter på backend..."
for i in {1..30}; do
    if health_check; then
        echo "✅ Backend er klar!"
        break
    fi
    sleep 2
done

# Hold prosessen i live
wait $BACKEND_PID 
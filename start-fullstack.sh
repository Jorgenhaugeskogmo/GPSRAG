#!/bin/bash

# Sett PORT fallback
export PORT=${PORT:-8000}
export FRONTEND_PORT=$((PORT + 1))

echo "🚀 Starter GPSRAG Fullstack på port $PORT"

# Start Next.js frontend i bakgrunn
cd /app/frontend
if [ -f "server.js" ]; then
    echo "📱 Starter Next.js frontend på port $FRONTEND_PORT"
    PORT=$FRONTEND_PORT node server.js &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    
    # Vent litt for frontend å starte
    sleep 3
fi

# Start backend med fullstack konfiguration
cd /app/backend
echo "🔧 Starter FastAPI backend på port $PORT"

# Cleanup function
cleanup() {
    echo "🛑 Stopper tjenester..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap cleanup on termination
trap cleanup SIGTERM SIGINT

# Start backend
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT 
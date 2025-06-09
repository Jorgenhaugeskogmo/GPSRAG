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
    
    # Vent på at frontend starter
    echo "Venter på at frontend starter..."
    sleep 5
    
    # Sjekk om frontend er tilgjengelig
    for i in {1..10}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            echo "✅ Frontend er tilgjengelig på port $FRONTEND_PORT"
            break
        else
            echo "Frontend ikke klar ennå, venter... ($i/10)"
            sleep 2
        fi
    done
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
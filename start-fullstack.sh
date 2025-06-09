#!/bin/bash

# Sett miljøvariabler for Railway
export PORT=${PORT:-8000}
export DATABASE_URL=${DATABASE_URL:-"sqlite:///./data/gpsrag.db"}
export RAILWAY_STATIC_URL=${RAILWAY_STATIC_URL:-"https://gpsrag-production.up.railway.app"}

echo "🚀 Starter GPSRAG Fullstack på port $PORT"
echo "📊 Database: $DATABASE_URL"
echo "🌐 Base URL: $RAILWAY_STATIC_URL"

# Opprett SQLite database hvis den ikke finnes
mkdir -p /app/data
touch /app/data/gpsrag.db

# Gå til backend mappen
cd /app/backend

echo "🔧 Initialiserer SQLite database..."
python -c "
from src.database import engine, Base
Base.metadata.create_all(bind=engine)
print('✅ Database tabeller opprettet')
"

echo "🎯 Starter integrert fullstack applikasjon på port $PORT"

# Start FastAPI som serverer både API og frontend
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info 
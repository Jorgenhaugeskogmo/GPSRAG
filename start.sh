#!/bin/bash

# Sett PORT fallback
export PORT=${PORT:-8000}

# Erstatt PORT i nginx config
sed -i "s/\$PORT/$PORT/g" /etc/nginx/sites-available/default

# Start nginx i bakgrunnen
nginx &

# Start backend API
cd /app/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT 
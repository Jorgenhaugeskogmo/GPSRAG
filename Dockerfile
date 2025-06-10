# GPSRAG Railway Deployment - Backend only med frontend serving
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./

# Installer frontend dependencies med cache optimalisering
RUN npm ci --no-audit --progress=false

COPY frontend/ ./

# Bygg frontend for produksjon
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Python Backend 
FROM python:3.11-slim

# Installer kun nødvendige system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Kopier requirements.txt først for bedre caching
COPY api/requirements.txt ./requirements.txt

# Installer Python dependencies med minneoptimalisering
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Kopier backend kode
COPY api/ ./backend/

# Kopier frontend build for serving fra backend
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json

# Lag startup script for Railway - kun backend som serverer alt
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starter GPSRAG Fullstack Backend på Railway..."\n\
echo "Port: $PORT"\n\
cd /app/backend && python -m uvicorn index:app --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Eksponer port
EXPOSE $PORT

# Start kun backend (som serverer frontend)
CMD ["/app/start.sh"] 
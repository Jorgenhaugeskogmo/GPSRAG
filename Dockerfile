# GPSRAG Railway Deployment - Memory optimiert
FROM node:18-alpine AS frontend-builder

# Sett memory limits for Node.js
ENV NODE_OPTIONS="--max_old_space_size=1024"

WORKDIR /app/frontend
COPY frontend/package*.json ./

# Installer frontend dependencies med cache optimalisering
RUN npm ci --no-audit --progress=false --prefer-offline

COPY frontend/ ./

# Bygg frontend for produksjon med memory optimalisering
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
COPY requirements.txt ./

# Installer Python dependencies med minneoptimalisering
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Kopier backend kode
COPY api/ ./

# Kopier frontend build fra forrige stage
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-builder /app/frontend/next.config.js ./frontend/next.config.js

# Lag startup script for Railway
RUN echo '#!/bin/bash\n\
echo "🚀 Starter GPSRAG på Railway..."\n\
echo "Starter FastAPI backend på port $PORT"\n\
exec python -m uvicorn index:app --host 0.0.0.0 --port $PORT\n\
' > start.sh && chmod +x start.sh

# Eksponér Railway port
EXPOSE $PORT

# Start applikasjonen
CMD ["./start.sh"] 
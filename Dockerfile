# GPSRAG Railway Deployment - Optimalisert for minne og hastighet
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

# Installer Node.js 18 (for serving frontend)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

WORKDIR /app

# Kopier requirements.txt først for bedre caching
COPY api/requirements.txt ./requirements.txt

# Installer Python dependencies med minneoptimalisering
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Kopier backend kode
COPY api/ ./backend/

# Kopier frontend build
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/

# Lag startup script for Railway
RUN echo '#!/bin/bash\n\
cd /app/frontend && npm start &\n\
cd /app/backend && python -m uvicorn index:app --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Eksponer port
EXPOSE $PORT

# Start begge tjenester
CMD ["/app/start.sh"] 
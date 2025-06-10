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

# Kopier frontend build OG node_modules for serving
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# Lag startup script for Railway med bedre feilhåndtering
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starter GPSRAG på Railway..."\n\
echo "Frontend: npm start i bakgrunnen"\n\
cd /app/frontend && npm start &\n\
echo "Backend: Starting FastAPI på port $PORT"\n\
cd /app/backend && python -m uvicorn index:app --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Eksponer port
EXPOSE $PORT

# Start begge tjenester
CMD ["/app/start.sh"] 
# GPSRAG Fullstack Deployment - Frontend + Backend Integrert
# Komplett løsning for Railway deployment

# Stage 1: Bygg Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Bygg frontend for produksjon med riktig API URL
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL="https://gpsrag-production.up.railway.app"
ENV NEXT_PUBLIC_WS_URL="wss://gpsrag-production.up.railway.app"
RUN npm run build

# Stage 2: Python Backend med Frontend
FROM python:3.11-slim

# Installer system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Installer Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Opprett app directory
WORKDIR /app

# Kopier og installer Python dependencies
COPY services/api-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Installer ekstra dependencies for Railway
RUN pip install aiofiles sqlalchemy[sqlite]

# Kopier backend kode
COPY services/api-gateway/ ./backend/

# Kopier standalone frontend build
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# Opprett Railway-spesifikk startup script
COPY start-fullstack.sh ./start-fullstack.sh
RUN chmod +x ./start-fullstack.sh

# Lag SQLite database directory
RUN mkdir -p /app/data

# Eksponer port
EXPOSE $PORT

# Start fullstack app
CMD ["./start-fullstack.sh"] 
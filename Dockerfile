# GPSRAG Fullstack Deployment - Frontend + Backend Integrert
# Komplett løsning for Railway deployment

# Stage 1: Bygg Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Bygg frontend for produksjon
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_WS_URL=""
RUN npm run build

# Stage 2: Python Backend med Frontend
FROM python:3.11-slim

# Installer system dependencies inkludert Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Opprett app directory
WORKDIR /app

# Kopier og installer Python dependencies
COPY services/api-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Installer FastAPI ekstra dependencies for statiske filer
RUN pip install aiofiles

# Kopier backend kode
COPY services/api-gateway/ ./backend/

# Kopier bygget frontend (statisk export)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# Opprett startup script
COPY start-fullstack.sh ./start-fullstack.sh
RUN chmod +x ./start-fullstack.sh

# Eksponer port
EXPOSE $PORT

# Start fullstack app
CMD ["./start-fullstack.sh"] 
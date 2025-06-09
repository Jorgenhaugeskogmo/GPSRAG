# GPSRAG Full Stack Deployment - Frontend + Backend
# Multi-stage build for complete solution on Railway

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Set production API URL for build
ENV NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_WS_URL=/ws
RUN npm run build

# Stage 2: Python Backend with Frontend
FROM python:3.11-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    supervisor \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Create app structure
WORKDIR /app

# Copy Python dependencies and install
COPY services/api-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY services/api-gateway/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/.next/standalone ./frontend/
COPY --from=frontend-build /app/frontend/.next/static ./frontend/.next/static/
COPY --from=frontend-build /app/frontend/public ./frontend/public/

# Copy configuration files
COPY nginx.conf /etc/nginx/sites-available/gpsrag
COPY supervisord.conf /etc/supervisor/conf.d/gpsrag.conf
COPY start.sh /app/start.sh

RUN ln -s /etc/nginx/sites-available/gpsrag /etc/nginx/sites-enabled/
RUN rm -f /etc/nginx/sites-enabled/default
RUN chmod +x /app/start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Start application
CMD ["/app/start.sh"] 
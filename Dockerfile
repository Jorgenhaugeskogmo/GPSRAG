# GPSRAG Railway Deployment - Simplified Single Container
# Backend API med statiske frontend filer

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Sett produksjon miljøvariabler
ENV NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_WS_URL=/ws
ENV NODE_ENV=production

RUN npm run build

# Stage 2: Python Backend med statiske filer
FROM python:3.11-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python dependencies and install
COPY services/api-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY services/api-gateway/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/.next/standalone ./frontend/
COPY --from=frontend-build /app/frontend/.next/static ./frontend/.next/static/
COPY --from=frontend-build /app/frontend/public ./frontend/public/

# Create nginx config
RUN mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Start the application
CMD ["/start.sh"] 
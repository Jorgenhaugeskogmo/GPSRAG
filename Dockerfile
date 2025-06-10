# GPSRAG Railway Deployment - API Gateway Edition
FROM node:18-alpine AS frontend-builder

# Set memory limits for Node.js - optimized for Railway
ENV NODE_OPTIONS="--max_old_space_size=1536"
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app/frontend
COPY frontend/package*.json ./

# Install frontend dependencies (include dev dependencies for Tailwind plugins)
RUN npm ci --no-audit --progress=false

COPY frontend/ ./

# Build frontend for production
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Python API Gateway
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies (Railway optimized) with FORCED NumPy compatibility
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# FORCE NumPy 1.x for ChromaDB compatibility - NO EXCEPTIONS!
RUN pip install --no-cache-dir "numpy==1.24.3" --force-reinstall

# Install requirements with NumPy already fixed
RUN pip install --no-cache-dir -r requirements.txt

# Copy API Gateway code
COPY services/api-gateway/ ./

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/next.config.js ./frontend/
COPY --from=frontend-builder /app/frontend/package.json ./frontend/

# Environment variables for Railway
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV DATABASE_URL=sqlite:///./gpsrag.db
ENV ENVIRONMENT=railway

# Railway port configuration (Railway sets PORT automatically)
ENV PORT=${PORT:-8080}
EXPOSE ${PORT:-8080}

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["sh", "-c", "curl -f http://localhost:${PORT:-8080}/health || exit 1"]

# Start API Gateway with Railway PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"] 
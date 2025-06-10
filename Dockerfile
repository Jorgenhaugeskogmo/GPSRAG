# GPSRAG Railway Deployment - Absolute minimal memory
FROM node:18-alpine AS frontend-builder

# Minimal memory for Node.js
ENV NODE_OPTIONS="--max_old_space_size=256"
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app/frontend
COPY frontend/package*.json ./

# Installer kun production dependencies
RUN npm ci --only=production --no-audit --progress=false

COPY frontend/ ./

# Minimal build
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Minimal Python Backend
FROM python:3.11-alpine

# Minimal system dependencies
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

# Copy minimal requirements
COPY requirements-minimal.txt requirements.txt

# Ultra-minimal pip installation
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --no-deps fastapi uvicorn pydantic
RUN pip install --no-cache-dir python-multipart python-dotenv aiofiles

# Copy minimal API code
COPY api/ ./api/

# Copy minimal frontend
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next

# Expose port
EXPOSE 8080

# Minimal start command
CMD ["python", "-m", "uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080"] 
# GPSRAG Railway Deployment - Ultra memory optimalized 
FROM node:18-alpine AS frontend-builder

# Sett memory limits for Node.js - redusert for Railway
ENV NODE_OPTIONS="--max_old_space_size=512"
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app/frontend
COPY frontend/package*.json ./

# Installer frontend dependencies med aggressive memory optimization
RUN npm ci --no-audit --progress=false --prefer-offline --omit=dev

COPY frontend/ ./

# Bygg frontend for produksjon med memory optimalisering
ENV NODE_ENV=production
RUN npm run build --max_old_space_size=512

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

# Memory-optimized pip installation - installer i separate steg
# Upgrade pip først
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installer core dependencies først (minst memory-intensive)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.8.2 \
    python-multipart==0.0.6

# Installer AI dependencies separat
RUN pip install --no-cache-dir \
    openai==1.26.0

# Installer Weaviate separat
RUN pip install --no-cache-dir \
    weaviate-client==4.15.0

# Installer LangChain dependencies separat
RUN pip install --no-cache-dir \
    langchain-core==0.2.43 \
    langchain-openai==0.1.8

# Installer resterende dependencies
RUN pip install --no-cache-dir \
    pypdf==4.2.0 \
    python-dotenv==1.0.0 \
    aiofiles==23.1.0

# Kopier API kode
COPY api/ ./api/

# Kopier built frontend fra forrige stage
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/

# Lag frontend static directory for serving
RUN mkdir -p ./static

# Expose Railway port
EXPOSE 8080

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start kommando - kun backend
CMD ["python", "-m", "uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080"] 
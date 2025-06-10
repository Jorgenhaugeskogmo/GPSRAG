# GPSRAG Railway Deployment - NO FRONTEND BUILD (ultra minimal memory)
FROM python:3.11-alpine

# Minimal system dependencies
RUN apk add --no-cache gcc musl-dev curl

WORKDIR /app

# Copy minimal requirements
COPY requirements-minimal.txt requirements.txt

# Ultra-minimal pip installation - one by one to minimize memory spikes
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir fastapi==0.104.1
RUN pip install --no-cache-dir uvicorn==0.24.0  
RUN pip install --no-cache-dir pydantic==2.8.2
RUN pip install --no-cache-dir python-multipart==0.0.6
RUN pip install --no-cache-dir python-dotenv==1.0.0
RUN pip install --no-cache-dir aiofiles==23.1.0

# Copy API code
COPY api/ ./api/

# Create minimal index.html for basic web interface (NO React/Next.js)
RUN mkdir -p ./static
RUN echo '<!DOCTYPE html><html><head><title>GPSRAG API</title></head><body><h1>GPSRAG API is running</h1><p>Backend API is available at /docs for testing</p></body></html>' > ./static/index.html

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=2 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start only backend - no frontend
CMD ["python", "-m", "uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080"] 
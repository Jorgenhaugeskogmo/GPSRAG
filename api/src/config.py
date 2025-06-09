"""
Konfigurasjon for GPSRAG API Gateway
"""

import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Applikasjonens innstillinger"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    
    # App settings
    app_name: str = "GPSRAG API"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"
    
    # Database - Use SQLite for Railway deployment
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./gpsrag.db")
    
    # Vector Database
    weaviate_url: str = "http://weaviate:8080"
    weaviate_api_key: Optional[str] = None
    
    # Object Storage - Disabled for Railway
    minio_url: str = os.getenv("MINIO_URL", "")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "")
    minio_bucket_name: str = "documents"
    
    # Redis Cache
    redis_url: str = "redis://redis:6379"
    
    # AI/ML
    huggingface_api_key: Optional[str] = None
    
    # Security
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File uploads
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: list = [
        "application/pdf",
        "text/plain",
        "application/json",
        "text/csv"
    ]
    
    # RAG settings
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # External Services - Disabled for Railway
    rag_engine_url: str = os.getenv("RAG_ENGINE_URL", "http://localhost:8002")
    visualization_url: str = os.getenv("VISUALIZATION_URL", "http://localhost:8003")
    
    # CORS Origins
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "https://*.railway.app"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 
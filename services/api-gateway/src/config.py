"""
Konfigurasjon for GPSRAG API Gateway
"""

from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Applikasjonens innstillinger"""
    
    # App settings
    app_name: str = "GPSRAG API"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql://postgres:postgres@postgres:5432/gpsrag"
    
    # Vector Database
    weaviate_url: str = "http://weaviate:8080"
    weaviate_api_key: Optional[str] = None
    
    # Object Storage
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "gpsrag-data"
    minio_secure: bool = False
    
    # Redis Cache
    redis_url: str = "redis://redis:6379"
    
    # AI/ML
    openai_api_key: Optional[str] = None
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
    
    # Services
    ingestion_service_url: str = "http://ingestion:8001"
    rag_engine_url: str = "http://rag-engine:8002"
    visualization_service_url: str = "http://visualization:8003"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 
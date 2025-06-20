"""
Database konfigurasjon og modeller for GPSRAG
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uuid
from datetime import datetime
from typing import Generator

from .config import settings

# Create database engine
# SQLite configuration for Railway deployment
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug if hasattr(settings, 'debug') else False
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug if hasattr(settings, 'debug') else False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class User(Base):
    """Bruker modell"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="uploaded_by_user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class Document(Base):
    """Dokument modell"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    content_type = Column(String(100))
    file_size = Column(Integer)
    status = Column(String(50), default='uploaded')
    chunk_count = Column(Integer, default=0)
    uploaded_by = Column(String(36), ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    gps_data = relationship("GPSData", back_populates="document")
    embeddings = relationship("Embedding", back_populates="document")

class GPSData(Base):
    """GPS data modell"""
    __tablename__ = "gps_data"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(100))
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    altitude = Column(DECIMAL(10, 2))
    speed = Column(DECIMAL(8, 2))
    heading = Column(DECIMAL(5, 2))
    accuracy = Column(DECIMAL(8, 2))
    timestamp = Column(DateTime, nullable=False)
    gps_metadata = Column(JSON)
    document_id = Column(String(36), ForeignKey("documents.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="gps_data")

class ChatSession(Base):
    """Chat session modell"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    """Chat melding modell"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"))
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class Embedding(Base):
    """Embedding metadata modell"""
    __tablename__ = "embeddings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    text_content = Column(Text, nullable=False)
    vector_id = Column(String(255), unique=True)  # Reference to Weaviate
    embedding_model = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")

class Visualization(Base):
    """Visualisering modell"""
    __tablename__ = "visualizations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    chart_type = Column(String(100), nullable=False)
    data_query = Column(Text)
    chart_config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
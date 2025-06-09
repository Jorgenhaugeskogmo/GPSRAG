"""
Pydantic schemas for chat API
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ChatSessionCreate(BaseModel):
    """Schema for å opprette en ny chat-session"""
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    """Schema for chat-session respons"""
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    """Schema for å opprette en ny chat-melding"""
    content: str
    role: str  # user, assistant, system
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    """Schema for chat-melding respons"""
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    """Schema for chat-forespørsel"""
    message: str
    session_id: Optional[str] = None
    include_gps_data: bool = False
    metadata: Optional[Dict[str, Any]] = None

class DocumentSource(BaseModel):
    """Schema for dokument-kilde"""
    filename: str
    page: Optional[int] = None
    relevance_score: float
    excerpt: str

class ChatResponse(BaseModel):
    """Schema for chat-respons"""
    response: str
    sources: List[DocumentSource] = []
    confidence: float = 0.0
    session_id: str
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Source(BaseModel):
    """Schema for kilde-referanse"""
    document_id: UUID
    document_name: str
    page_number: Optional[int] = None
    relevance_score: float
    excerpt: str 
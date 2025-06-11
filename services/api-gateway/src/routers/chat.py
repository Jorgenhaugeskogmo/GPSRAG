"""
Chat API endepunkter for GPSRAG
Håndterer chat-sessioner og meldinger med RAG-funksjonalitet
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import httpx
import logging
from pydantic import BaseModel
import json
import uuid
import os
from datetime import datetime

from ..database import get_db, ChatSession, ChatMessage, User
from ..config import settings
from ..schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    DocumentSource
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """Opprett en ny chat-session"""
    try:
        # TODO: Implementer autentisering og få bruker-ID
        user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        db_session = ChatSession(
            user_id=user_id,
            title=session_data.title or "Ny Chat"
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return ChatSessionResponse(
            id=db_session.id,
            title=db_session.title,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    except Exception as e:
        logger.error(f"Feil ved opprettelse av chat-session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke opprette chat-session"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Hent alle chat-sessioner for bruker"""
    try:
        # TODO: Filtrer på bruker-ID etter autentisering
        sessions = db.query(ChatSession)\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return [
            ChatSessionResponse(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Feil ved henting av chat-sessioner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke hente chat-sessioner"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Hent alle meldinger for en chat-session"""
    try:
        # Verifiser at session eksisterer
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat-session ikke funnet"
            )
        
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.timestamp)\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return [
            ChatMessageResponse(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                metadata=message.metadata,
                timestamp=message.timestamp
            )
            for message in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feil ved henting av chat-meldinger: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke hente chat-meldinger"
        )

@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    session_id: UUID,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send en chat-melding og få svar med RAG"""
    try:
        # Import RAG service
        from rag_service import get_rag_service
        rag_service = get_rag_service()
        
        # Lagre bruker-melding
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        db.commit()
        
        # Søk etter relevante dokumenter
        relevant_docs = await rag_service.search_documents(
            query=chat_request.message,
            top_k=3
        )
        
        if not relevant_docs:
            # Ingen relevante dokumenter funnet
            response = {
                "response": "Beklager, jeg fant ingen relevante dokumenter for spørsmålet ditt. Last opp noen PDF-er først!",
                "sources": [],
                "context_used": False
            }
        else:
            # Generer svar med RAG
            try:
                response = await rag_service.generate_rag_response(
                    query=chat_request.message,
                    relevant_docs=relevant_docs
                )
            except Exception as e:
                logger.error(f"❌ RAG respons generering feilet: {e}")
                # Fallback til enkel respons
                response = {
                    "response": "Beklager, jeg kunne ikke generere et svar basert på dokumentene akkurat nå. Prøv igjen senere!",
                    "sources": [],
                    "context_used": False,
                    "error": str(e)
                }
        
        # Lagre assistant-melding
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response["response"],
            metadata={
                "sources": response.get("sources", []),
                "context_used": response.get("context_used", False),
                "error": response.get("error", None)
            }
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            message=response["response"],
            sources=response.get("sources", []),
            context_used=response.get("context_used", False)
        )
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Det oppstod en feil under chat-prosessering"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Slett en chat-session og alle tilhørende meldinger"""
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat-session ikke funnet"
            )
        
        # Slett alle meldinger (cascade skal håndtere dette)
        db.delete(session)
        db.commit()
        
        return {"message": "Chat-session slettet"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feil ved sletting av chat-session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke slette chat-session"
        )

@router.post("/chat/", response_model=ChatResponse)
async def simple_chat_endpoint(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Forenklet chat-endepunkt for å matche frontend"""
    try:
        from ...rag_service import get_rag_service # Adjusted import path
        rag_service = get_rag_service()

        # Generate RAG response
        rag_data = await rag_service.generate_rag_response(chat_request.message)

        # Basic session/message logging (optional, can be expanded)
        # Note: This is a simplified version. A full implementation would
        # properly create/manage sessions and messages in the DB.
        logger.info(f"Chat in session {chat_request.session_id}: {chat_request.message}")

        return ChatResponse(
            response=rag_data["response"],
            session_id=chat_request.session_id,
            sources=rag_data.get("sources", []),
            context_used=rag_data.get("context_used", False)
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal chat error occurred: {e}")

@router.get("/sessions")
async def list_chat_sessions(db: Session = Depends(get_db)):
    """List alle chat-sesjoner"""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    
    return [
        {
            "id": str(session.id),
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(session.messages)
        }
        for session in sessions
    ]

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Hent alle meldinger for en sesjon"""
    try:
        session_uuid = uuid.UUID(session_id)
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_uuid
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.message_metadata
            }
            for msg in messages
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig sesjons-ID")

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Slett en chat-sesjon og alle tilhørende meldinger"""
    try:
        session_uuid = uuid.UUID(session_id)
        session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesjon ikke funnet")
        
        # Slett alle meldinger først (pga foreign key constraint)
        db.query(ChatMessage).filter(ChatMessage.session_id == session_uuid).delete()
        
        # Slett sesjonen
        db.delete(session)
        db.commit()
        
        return {"message": "Chat-sesjon slettet"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig sesjons-ID") 
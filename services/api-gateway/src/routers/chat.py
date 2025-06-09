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
router = APIRouter(prefix="/chat", tags=["chat"])

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
    """Send en melding og få RAG-basert svar"""
    try:
        # Verifiser at session eksisterer
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat-session ikke funnet"
            )
        
        # Lagre bruker-melding
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=chat_request.message,
            metadata=chat_request.metadata
        )
        db.add(user_message)
        db.commit()
        
        # Kall RAG-engine for å få svar
        try:
            async with httpx.AsyncClient() as client:
                rag_response = await client.post(
                    f"{settings.rag_engine_url}/query",
                    json={
                        "query": chat_request.message,
                        "session_id": str(session_id),
                        "include_gps": chat_request.include_gps_data,
                        "metadata": chat_request.metadata
                    },
                    timeout=30.0
                )
                rag_response.raise_for_status()
                rag_data = rag_response.json()
        except Exception as e:
            logger.error(f"Feil ved kall til RAG-engine: {e}")
            # Fallback-svar hvis RAG-engine ikke er tilgjengelig
            rag_data = {
                "response": "Beklager, jeg kan ikke svare på det akkurat nå. Prøv igjen senere.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Lagre assistant-melding
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=rag_data["response"],
            metadata={
                "sources": rag_data.get("sources", []),
                "confidence": rag_data.get("confidence", 0.0),
                "processing_time": rag_data.get("processing_time", 0.0)
            }
        )
        db.add(assistant_message)
        db.commit()
        
        # Konverter kilder til riktig format
        formatted_sources = []
        if isinstance(rag_data.get("sources", []), list):
            for source in rag_data.get("sources", []):
                try:
                    # Handle both dict and object formats
                    if isinstance(source, dict):
                        formatted_sources.append(DocumentSource(
                            filename=source.get("filename", "Ukjent dokument"),
                            page=source.get("page"),
                            relevance_score=source.get("score", 0.0),  # RAG engine uses "score"
                            excerpt=source.get("excerpt", "")
                        ))
                    else:
                        # If it's already a source object, extract the data
                        formatted_sources.append(DocumentSource(
                            filename=getattr(source, "filename", "Ukjent dokument"),
                            page=getattr(source, "page", None),
                            relevance_score=getattr(source, "score", 0.0),
                            excerpt=getattr(source, "excerpt", "")
                        ))
                except Exception as e:
                    logger.error(f"Error formatting source: {e}, source: {source}")
                    continue
        
        return ChatResponse(
            response=rag_data["response"],
            session_id=str(session_id),
            sources=formatted_sources,
            metadata=rag_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feil ved behandling av chat-melding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke behandle meldingen"
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

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send en melding til RAG-systemet og få svar"""
    
    try:
        # Opprett eller finn eksisterende chat-sesjon
        session_id = request.session_id or str(uuid.uuid4())
        
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == uuid.UUID(session_id)
        ).first()
        
        if not chat_session:
            chat_session = ChatSession(
                id=uuid.UUID(session_id),
                user_id=None,  # TODO: Implementer brukerautentisering
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        # Lagre brukermelding
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            role="user",
            content=request.message,
            message_metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        db.add(user_message)
        db.commit()
        
        # Send til RAG-motoren
        try:
            async with httpx.AsyncClient() as client:
                rag_response = await client.post(
                    f"http://rag-engine:8002/query",
                    json={
                        "question": request.message,
                        "session_id": session_id,
                        "include_sources": True
                    },
                    timeout=30.0
                )
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    logger.info(f"RAG Response: {rag_data}")  # Debug logging
                    ai_response = rag_data.get("answer", "Beklager, jeg kunne ikke prosessere forespørselen din.")
                    sources = rag_data.get("sources", [])
                    logger.info(f"Sources: {sources}")  # Debug logging
                    metadata = rag_data.get("metadata", {})
                else:
                    # Fallback ved feil i RAG-motoren
                    ai_response = generate_fallback_response(request.message)
                    sources = []
                    metadata = {"fallback": True, "rag_error": rag_response.status_code}
                    
        except Exception as e:
            print(f"RAG engine error: {e}")
            # Fallback ved nettverksfeil
            ai_response = generate_fallback_response(request.message)
            sources = []
            metadata = {"fallback": True, "error": str(e)}
        
        # Lagre AI-respons
        ai_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            role="assistant",
            content=ai_response,
            message_metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "sources": sources,
                "metadata": metadata
            }
        )
        db.add(ai_message)
        db.commit()
        
        # Konverter kilder til riktig format
        formatted_sources = []
        if isinstance(sources, list):
            for source in sources:
                try:
                    # Handle both dict and object formats
                    if isinstance(source, dict):
                        formatted_sources.append(DocumentSource(
                            filename=source.get("filename", "Ukjent dokument"),
                            page=source.get("page"),
                            relevance_score=source.get("score", 0.0),  # RAG engine uses "score"
                            excerpt=source.get("excerpt", "")
                        ))
                    else:
                        # If it's already a source object, extract the data
                        formatted_sources.append(DocumentSource(
                            filename=getattr(source, "filename", "Ukjent dokument"),
                            page=getattr(source, "page", None),
                            relevance_score=getattr(source, "score", 0.0),
                            excerpt=getattr(source, "excerpt", "")
                        ))
                except Exception as e:
                    logger.error(f"Error formatting source: {e}, source: {source}")
                    continue
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            sources=formatted_sources,
            metadata=metadata
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Kunne ikke prosessere chat-meldingen")

def generate_fallback_response(message: str) -> str:
    """Generer en fallback-respons når RAG-motoren ikke er tilgjengelig"""
    
    message_lower = message.lower()
    
    # GPS/GNSS relaterte spørsmål
    if any(word in message_lower for word in ['gps', 'gnss', 'satelitt', 'posisjon']):
        return """GPS (Global Positioning System) er et satellittnavigasjonssystem som gir posisjonsinformasjon. 
        
For nøyaktig informasjon om u-blox moduler og konfigurering, vennligst last opp den relevante brukermanualen først, 
så kan jeg gi deg spesifikke svar basert på dokumentasjonen."""
    
    # u-blox relaterte spørsmål
    elif any(word in message_lower for word in ['u-blox', 'ublox', 'modul', 'chip']):
        return """u-blox lager høyytelse GNSS-moduler for posisjonering og tidsynkronisering.
        
For å få detaljert informasjon om spesifikke u-blox moduler, vennligst last opp brukermanualen for den aktuelle modulen 
i dokumentopplasting-fanen. Da kan jeg svare på spesifikke tekniske spørsmål."""
    
    # NMEA relaterte spørsmål
    elif any(word in message_lower for word in ['nmea', 'melding', 'protokoll']):
        return """NMEA 0183 er en standard kommunikasjonsprotokoll for marine elektroniske enheter, inkludert GPS-mottakere.
        
For spesifikke NMEA-meldinger som støttes av u-blox moduler, last opp den relevante dokumentasjonen så kan jeg gi deg 
detaljerte svar om protokollimplementering."""
    
    # Fallback for andre spørsmål
    else:
        return """Hei! Jeg er en AI-assistent som spesialiserer seg på GPS/GNSS-teknologi og u-blox moduler.
        
For å kunne gi deg presise svar, vennligst:
1. Last opp relevante brukermanualer eller dokumenter i 'Dokumentopplasting'-fanen
2. Still så spesifikke spørsmål om GPS, GNSS, u-blox moduler, eller innholdet i dokumentene du har lastet opp

Jeg kan hjelpe med tekniske spørsmål om posisjonering, konfigurasjon, NMEA-protokoller og mer!"""

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
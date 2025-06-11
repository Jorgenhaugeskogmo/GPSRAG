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

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat endpoint som frontend bruker - direkte RAG integration"""
    try:
        # Kall RAG-engine direkte
        rag_engine_url = os.getenv("RAG_ENGINE_URL", "http://rag-engine:8002")
        
        async with httpx.AsyncClient() as client:
            rag_response = await client.post(
                f"{rag_engine_url}/query",
                json={
                    "question": request.message,
                    "session_id": request.session_id or "default-session",
                    "include_sources": True,
                    "max_results": 5
                },
                timeout=30.0
            )
            
            if rag_response.status_code == 200:
                rag_data = rag_response.json()
                
                # Formater response som frontend forventer
                return ChatResponse(
                    response=rag_data.get("answer", "Beklager, jeg kunne ikke svare på det."),
                    session_id=request.session_id or "default-session",
                    sources=[
                        DocumentSource(
                            filename=source.get("filename", "Ukjent dokument"),
                            page=source.get("page"),
                            relevance_score=source.get("score", 0.0),
                            excerpt=source.get("excerpt", "")
                        )
                        for source in rag_data.get("sources", [])
                    ],
                    metadata=rag_data.get("metadata", {})
                )
            else:
                # Fallback hvis RAG engine feiler
                return ChatResponse(
                    response="Beklager, RAG-systemet er ikke tilgjengelig akkurat nå.",
                    session_id=request.session_id or "default-session",
                    sources=[],
                    metadata={"fallback": True}
                )
                
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        # Fallback respons
        return ChatResponse(
            response="Beklager, det oppstod en feil. Prøv igjen senere.",
            session_id=request.session_id or "default-session",
            sources=[],
            metadata={"error": str(e)}
        )

@router.post("/message", response_model=ChatResponse)
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
        
        # Send til RAG-motoren (med forbedret error handling for Railway)
        ai_response = None
        sources = []
        metadata = {"fallback": True, "platform": "Railway"}
        
        try:
            # Først prøv lokal RAG-engine (for Docker Compose)
            async with httpx.AsyncClient() as client:
                rag_response = await client.post(
                    f"http://rag-engine:8002/query",
                    json={
                        "question": request.message,
                        "session_id": session_id,
                        "include_sources": True
                    },
                    timeout=5.0  # Kort timeout for Railway
                )
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    logger.info(f"RAG Response: {rag_data}")
                    ai_response = rag_data.get("answer", "")
                    sources = rag_data.get("sources", [])
                    metadata = rag_data.get("metadata", {})
                    logger.info(f"Sources: {sources}")
                else:
                    ai_response = None
                    
        except Exception as e:
            logger.info(f"RAG engine ikke tilgjengelig (forventet på Railway): {e}")
            ai_response = None
        
        # Hvis RAG-engine ikke svarte, bruk fallback
        if not ai_response:
            ai_response = generate_fallback_response(request.message)
            metadata.update({"fallback_reason": "RAG engine ikke tilgjengelig på Railway"})
        
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
        logger.error(f"Chat error: {e}")
        # Returner fallback i stedet for å krasje
        fallback_response = generate_fallback_response(request.message if hasattr(request, 'message') else "Hei")
        return ChatResponse(
            response=fallback_response,
            session_id=request.session_id or str(uuid.uuid4()),
            sources=[],
            metadata={"fallback": True, "error": str(e), "platform": "Railway"}
        )

def generate_fallback_response(message: str) -> str:
    """Generer en fallback-respons når RAG-motoren ikke er tilgjengelig"""
    
    # På Railway: Bruk OpenAI direkte for å gi smarte svar
    try:
        import openai
        import os
        
        # Sett OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key != "your_openai_api_key_here":
            
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            
            # Lag en smart respons basert på GPS/GNSS kontekst
            system_prompt = """Du er en ekspert på GPS/GNSS teknologi og u-blox moduler. 
            Du hjelper brukere med tekniske spørsmål om posisjonering, NMEA-protokoller, 
            u-blox konfigurasjon og GPS-relaterte emner. Svar på norsk med teknisk presisjon."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
    except Exception as e:
        logger.info(f"OpenAI fallback feilet: {e}")
    
    # Hvis OpenAI feiler, bruk statiske svar
    message_lower = message.lower()
    
    # GPS/GNSS relaterte spørsmål
    if any(word in message_lower for word in ['gps', 'gnss', 'satelitt', 'posisjon']):
        return """GPS (Global Positioning System) er et satellittnavigasjonssystem som gir posisjonsinformasjon. 

🛰️ **GPS Grunnleggende:**
- GPS bruker minst 4 satellitter for å beregne posisjon
- Nøyaktighet: 1-5 meter under normale forhold
- GNSS inkluderer GPS, GLONASS, Galileo og BeiDou

🔧 **For u-blox moduler:**
- Konfigurer via UBX-protokoll eller u-center software
- NMEA 0183 for standard output
- Støtter RTK for cm-nøyaktighet

Har du spesifikke spørsmål om konfigurasjon eller implementering?"""
    
    # u-blox relaterte spørsmål
    elif any(word in message_lower for word in ['u-blox', 'ublox', 'modul', 'chip']):
        return """u-blox lager høyytelse GNSS-moduler for presise posisjonsapplikasjoner.

📡 **Populære u-blox moduler:**
- **ZED-F9P**: Multi-band RTK, cm-nøyaktighet
- **NEO-M8**: Standard precision, 2.5m CEP
- **MAX-M10S**: Lavt strømforbruk, 1.5m CEP

⚙️ **Konfigurering:**
- Bruk u-center software for setup
- UBX-CFG meldinger for programmatisk konfigurasjon
- UART/I2C/SPI kommunikasjon

Hvilket u-blox modul jobber du med? Kan hjelpe med spesifikk konfigurasjon!"""
    
    # NMEA relaterte spørsmål
    elif any(word in message_lower for word in ['nmea', 'melding', 'protokoll']):
        return """NMEA 0183 er standard protokoll for GPS-kommunikasjon.

📋 **Vanlige NMEA-meldinger:**
- **GGA**: Posisjon, høyde, satellitter i bruk
- **RMC**: Anbefalt minimum data (tid, pos, hastighet)
- **GSA**: Satelitt-status og DOP-verdier
- **GSV**: Satellitter i sikt med SNR

🔧 **u-blox NMEA konfigurasjon:**
- CFG-MSG for å aktivere/deaktivere meldinger
- Standard baudrate: 9600 (kan endres til 115200)
- Format: $GPGGA,... med checksum

Trenger du hjelp med parsing eller spesifikke NMEA-meldinger?"""
    
    # RTK relaterte spørsmål  
    elif any(word in message_lower for word in ['rtk', 'nøyaktighet', 'presisjon']):
        return """RTK (Real-Time Kinematic) gir centimeter-nøyaktighet!

📍 **RTK Grunnleggende:**
- Krever base station med kjent posisjon
- Korreksjonsdata via radio/internet (NTRIP)
- u-blox ZED-F9P støtter multi-band RTK

⚡ **Setup RTK:**
1. Konfigurer base station (Survey-in mode)
2. Send RTCM korreksjonsdata til rover
3. Oppnå Fixed solution for cm-nøyaktighet

🌐 **NTRIP caster:**
- Kartverket tilbyr CPOS tjeneste i Norge
- Standard port 2101, brukernavn/passord påkrevd

Jobber du med RTK base station eller rover setup?"""
    
    # Fallback for andre spørsmål
    else:
        return """🛰️ **Hei! Jeg er din GPS/GNSS assistent**

Jeg kan hjelpe deg med:

🔧 **Tekniske emner:**
- u-blox modul konfigurasjon
- NMEA protokoll og meldinger  
- RTK setup for høy nøyaktighet
- GPS/GNSS teori og implementering

📡 **Spesialiteter:**
- ZED-F9P RTK konfigurasjon
- UBX protokoll kommandoer
- NTRIP og korreksjonsdata
- Antenna design og plassering

Hva kan jeg hjelpe deg med i dag? Still gjerne spesifikke spørsmål om GPS/GNSS teknologi! 🚀"""

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
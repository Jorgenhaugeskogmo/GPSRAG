"""
Dokument-administrasjon API
Håndterer opplasting, prosessering og administrasjon av dokumenter
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import logging

from ..database import get_db
from ..models.documents import Document
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Last opp et dokument for prosessering"""
    try:
        # Valider filtype
        allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Ikke støttet filtype")
        
        # Generer unik ID og filnavn
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
        file_path = f"{file_id}.{file_extension}"
        full_path = os.path.join(UPLOAD_DIR, file_path)
        
        # Lagre fil lokalt
        content = await file.read()
        with open(full_path, "wb") as f:
            f.write(content)
        
        # Opprett dokument i database
        document = Document(
            id=uuid.UUID(file_id),
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            content_type=file.content_type,
            status="uploaded"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Dokument lastet opp: {file.filename} ({file_id})")
        
        return {
            "document_id": file_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "Dokument lastet opp. Prosessering starter snart."
        }
        
    except Exception as e:
        logger.error(f"Feil ved opplasting av dokument: {e}")
        raise HTTPException(status_code=500, detail="Feil ved opplasting av dokument")

@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Hent alle dokumenter"""
    try:
        documents = db.query(Document).offset(skip).limit(limit).all()
        
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                    "file_size": doc.file_size,
                    "content_type": doc.content_type
                }
                for doc in documents
            ],
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Feil ved henting av dokumenter: {e}")
        raise HTTPException(status_code=500, detail="Feil ved henting av dokumenter")

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Hent informasjon om et spesifikt dokument"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")
        
        return {
            "id": str(document.id),
            "filename": document.filename,
            "status": document.status,
            "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "chunk_count": document.chunk_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feil ved henting av dokument {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Feil ved henting av dokument")

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Slett et dokument"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")
        
        # Slett lokal fil
        try:
            file_path = os.path.join(UPLOAD_DIR, document.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Kunne ikke slette fil: {e}")
        
        # Slett fra database
        db.delete(document)
        db.commit()
        
        logger.info(f"Dokument slettet: {document.filename} ({document_id})")
        
        return {"message": "Dokument slettet"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feil ved sletting av dokument {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Feil ved sletting av dokument") 
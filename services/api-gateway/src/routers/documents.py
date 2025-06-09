"""
Documents router - Håndterer dokumentopplasting og prosessering
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import minio
import PyPDF2
import io
import httpx
import json
from datetime import datetime

from ..database import get_db, Document
from ..config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

# MinIO client
minio_client = minio.Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure
)

BUCKET_NAME = "documents"

# Sørg for at bucket eksisterer
try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
except Exception as e:
    print(f"MinIO bucket error: {e}")

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Last opp og prosesser et dokument"""
    
    # Valider filtype
    if not file.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="Ikke støttet filtype")
    
    # Valider filstørrelse (10MB maks)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Filen er for stor (maks 10MB)")
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        # Generer unikt filnavn
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        
        # Last opp til MinIO
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(content),
            len(content),
            content_type=file.content_type
        )
        
        # Eksporter tekst fra PDF
        extracted_text = ""
        if file.filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(content)
        elif file.filename.lower().endswith('.txt'):
            extracted_text = content.decode('utf-8')
        
        # Lagre metadata i database
        document = Document(
            id=uuid.UUID(file_id),
            filename=file.filename,
            original_filename=file.filename,
            file_path=unique_filename,
            content_type=file.content_type,
            file_size=len(content),
            extracted_text=extracted_text,
            upload_status='completed',
            document_metadata={
                "original_filename": file.filename,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "processed": False
            },
            uploaded_by=None  # TODO: Implementer brukerautentisering
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Send til prosessering (RAG engine)
        try:
            await process_document_for_rag(file_id, extracted_text, file.filename)
            
            # Oppdater status
            document.document_metadata["processed"] = True
            db.commit()
            
        except Exception as e:
            print(f"RAG processing error: {e}")
            # Dokumentet er lastet opp, men ikke prosessert for RAG
        
        return {
            "id": str(document.id),
            "filename": document.filename,
            "status": "uploaded",
            "processed_for_rag": document.document_metadata.get("processed", False),
            "text_extracted": len(extracted_text) > 0
        }
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Kunne ikke laste opp dokumentet")

async def process_document_for_rag(file_id: str, text: str, filename: str):
    """Send dokument til RAG-motoren for vektorisering"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://rag-engine:8002/process-document",
                json={
                    "document_id": file_id,
                    "text": text,
                    "filename": filename,
                    "metadata": {
                        "source": "upload",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"RAG processing failed: {response.status_code}")
                
    except Exception as e:
        print(f"Failed to process document for RAG: {e}")
        raise

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Eksporter tekst fra PDF"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text.strip()
        
    except Exception as e:
        print(f"PDF text extraction error: {e}")
        return ""

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """List alle opplastede dokumenter"""
    documents = db.query(Document).all()
    
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "content_type": doc.content_type,
            "file_size": doc.file_size,
            "upload_date": doc.uploaded_at.isoformat(),
            "processed": doc.document_metadata.get("processed", False),
            "has_text": len(doc.extracted_text or "") > 0
        }
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Hent informasjon om et spesifikt dokument"""
    try:
        doc_uuid = uuid.UUID(document_id)
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")
            
        return {
            "id": str(document.id),
            "filename": document.filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "upload_date": document.uploaded_at.isoformat(),
            "extracted_text_length": len(document.extracted_text or ""),
            "metadata": document.document_metadata,
            "processed_for_rag": document.document_metadata.get("processed", False)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig dokument-ID")

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Slett et dokument"""
    try:
        doc_uuid = uuid.UUID(document_id)
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")
        
        # Slett fra MinIO
        try:
            minio_client.remove_object(BUCKET_NAME, document.file_path)
        except Exception as e:
            print(f"MinIO delete error: {e}")
        
        # Slett fra database
        db.delete(document)
        db.commit()
        
        return {"message": "Dokument slettet"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig dokument-ID") 
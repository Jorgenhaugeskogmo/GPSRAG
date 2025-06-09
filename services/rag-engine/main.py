"""
RAG Engine Service - Håndterer RAG-spørringer og AI-respons
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import weaviate
import openai
import os
from datetime import datetime
import uuid
import json
import re
from urllib.parse import urlparse
from weaviate.classes.config import Configure
from weaviate.classes.query import MetadataQuery, Filter

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GPSRAG RAG Engine",
    description="Håndterer RAG-spørringer og AI-respons",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:8000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfigurer OpenAI (fallback når ikke satt)
openai.api_key = os.getenv("OPENAI_API_KEY", "demo-key")

# Weaviate client setup
weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
weaviate_client = None

try:
    weaviate_client = weaviate.connect_to_local(
        host="weaviate",
        port=8080
    )
    logger.info("Weaviate client initialized")
except Exception as e:
    logger.error(f"Failed to connect to Weaviate: {e}")
    weaviate_client = None

class DocumentProcessRequest(BaseModel):
    document_id: str
    text: str
    filename: str
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    question: str
    session_id: str = None
    include_sources: bool = True
    max_results: int = 5

class DocumentSource(BaseModel):
    filename: str
    score: float
    excerpt: str
    page: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource] = []
    metadata: Dict[str, Any] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    weaviate_status = "connected" if weaviate_client else "disconnected"
    return {
        "status": "healthy", 
        "service": "rag-engine",
        "weaviate": weaviate_status
    }

@app.post("/process-document")
async def process_document(request: DocumentProcessRequest):
    """Prosesser et dokument for RAG-systemet"""
    
    try:
        if not weaviate_client:
            raise HTTPException(status_code=503, detail="Weaviate ikke tilgjengelig")
        
        # Split tekst i chunks
        chunks = split_text_into_chunks(request.text, chunk_size=500, overlap=50)
        
        # Opprett schema hvis det ikke eksisterer
        ensure_document_schema()
        
        # Lagre chunks i Weaviate
        documents = weaviate_client.collections.get("Document")
        
        # Individual insert instead of batch to avoid timeout
        successful_inserts = 0
        for i, chunk in enumerate(chunks):
            try:
                documents.data.insert({
                    "document_id": request.document_id,
                    "filename": request.filename,
                    "chunk_index": i,
                    "content": chunk,
                    "metadata": json.dumps(request.metadata),
                    "created_at": datetime.utcnow().isoformat()
                })
                successful_inserts += 1
            except Exception as e:
                logger.error(f"Error storing chunk {i}: {e}")
                continue
        
        logger.info(f"Processed document {request.filename}: {successful_inserts}/{len(chunks)} chunks stored successfully")
        
        return {
            "document_id": request.document_id,
            "chunks_created": successful_inserts,
            "total_chunks": len(chunks),
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Kunne ikke prosessere dokument: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Gjør en RAG-spørring mot dokumentene"""
    
    try:
        # Hvis Weaviate ikke er tilgjengelig, gi fallback-svar
        if not weaviate_client:
            return QueryResponse(
                answer=generate_fallback_answer(request.question),
                sources=[],
                metadata={"fallback": True, "reason": "weaviate_unavailable"}
            )
        
        # Søk i Weaviate
        search_results = search_documents(request.question, max_results=request.max_results)
        
        # Hvis ingen relevante dokumenter funnet
        if not search_results:
            return QueryResponse(
                answer=generate_fallback_answer(request.question),
                sources=[],
                metadata={"fallback": True, "reason": "no_relevant_documents"}
            )
        
        # Generer svar med OpenAI (eller fallback)
        answer = generate_answer_with_context(request.question, search_results)
        
        # Formater kilder
        sources = [
            DocumentSource(
                filename=result["filename"],
                score=result["score"],
                excerpt=result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                page=result.get("page")
            )
            for result in search_results[:3]  # Top 3 kilder
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "total_results": len(search_results),
                "query_timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        return QueryResponse(
            answer=generate_fallback_answer(request.question),
            sources=[],
            metadata={"fallback": True, "error": str(e)}
        )

def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split tekst i overlappende chunks"""
    
    # Rens tekst
    text = re.sub(r'\s+', ' ', text.strip())
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Prøv å slutte på en setning eller ord
        if end < len(text):
            # Finn siste punktum innen chunk
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
            else:
                # Finn siste mellomrom
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def ensure_document_schema():
    """Sørg for at Weaviate schema eksisterer"""
    
    try:
        # Sjekk om klassen allerede eksisterer
        if weaviate_client.collections.exists("Document"):
            logger.info("Document schema already exists")
            return
            
        # Opprett Document-klassen med v4 API
        weaviate_client.collections.create(
            name="Document",
            description="Document chunks for RAG system",
            vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
            properties=[
                {
                    "name": "document_id",
                    "dataType": ["text"],
                    "description": "Unique document identifier"
                },
                {
                    "name": "filename", 
                    "dataType": ["text"],
                    "description": "Original filename"
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "Index of this chunk within the document"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Text content of the chunk"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "JSON metadata"
                },
                {
                    "name": "created_at",
                    "dataType": ["text"],
                    "description": "Creation timestamp"
                }
            ]
        )
        logger.info("Created Document schema in Weaviate")
            
    except Exception as e:
        logger.error(f"Schema creation error: {e}")

def search_documents(query: str, max_results: int = 5) -> List[Dict]:
    """Søk i dokumenter med Weaviate"""
    
    try:
        # Get collection
        documents = weaviate_client.collections.get("Document")
        
        # Perform nearText search with v4 API
        result = documents.query.near_text(
            query=query,
            limit=max_results,
            return_metadata=MetadataQuery(certainty=True)
        )
        
        # Formater resultater
        formatted_results = []
        for doc in result.objects:
            try:
                formatted_results.append({
                    "document_id": doc.properties.get("document_id", ""),
                    "filename": doc.properties.get("filename", "Ukjent"),
                    "content": doc.properties.get("content", ""),
                    "score": doc.metadata.certainty if doc.metadata.certainty else 0.0,
                    "metadata": json.loads(doc.properties.get("metadata", "{}"))
                })
            except Exception as e:
                logger.error(f"Error formatting search result: {e}")
                continue
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def generate_answer_with_context(question: str, context_docs: List[Dict]) -> str:
    """Generer svar med OpenAI basert på kontekst"""
    
    # Hvis OpenAI ikke er konfigurert, bruk fallback
    if openai.api_key == "demo-key":
        return generate_contextual_fallback(question, context_docs)
    
    try:
        # Bygg kontekst fra dokumenter
        context = "\n\n".join([
            f"Fra {doc['filename']}:\n{doc['content']}"
            for doc in context_docs[:3]
        ])
        
        # OpenAI prompt med ny API
        from openai import OpenAI
        client = OpenAI(api_key=openai.api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du er en teknisk ekspert på GPS/GNSS og u-blox moduler. Svar på norsk basert på gitt dokumentasjon."},
                {"role": "user", "content": f"""Basert på følgende dokumenter, svar på spørsmålet på norsk. Vær spesifikk og teknisk korrekt.

Dokumenter:
{context}

Spørsmål: {question}"""}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return generate_contextual_fallback(question, context_docs)

def generate_contextual_fallback(question: str, context_docs: List[Dict]) -> str:
    """Generer svar basert på kontekst-dokumenter uten OpenAI"""
    
    if not context_docs:
        return generate_fallback_answer(question)
    
    # Finn mest relevant dokument
    best_doc = max(context_docs, key=lambda x: x.get("score", 0))
    
    return f"""Basert på dokumentet "{best_doc['filename']}" fant jeg følgende relevante informasjon:

{best_doc['content'][:400]}...

For mer detaljert informasjon, se dokumentet "{best_doc['filename']}". 

Merk: Dette er et automatisk generert svar basert på dokumentsøk. For presise tekniske detaljer, referer til den fullstendige dokumentasjonen."""

def generate_fallback_answer(question: str) -> str:
    """Generer generisk fallback-svar"""
    
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['gps', 'gnss', 'satelitt', 'posisjon']):
        return """GPS (Global Positioning System) er et satellittnavigasjonssystem som bruker en konstellasjon av satellitter for å gi posisjonsinformasjon. GNSS (Global Navigation Satellite System) er et mer generelt begrep som inkluderer GPS og andre systemer som GLONASS, Galileo og BeiDou.

For spesifikk informasjon om u-blox moduler, vennligst last opp den relevante brukermanualen."""
    
    elif any(word in question_lower for word in ['u-blox', 'ublox', 'modul', 'chip']):
        return """u-blox er en ledende leverandør av GNSS-mottakere, moduler og chips for posisjonering og trådløs kommunikasjon. Deres produkter brukes i alt fra biler til IoT-enheter.

For detaljert teknisk informasjon, last opp brukermanualen for den spesifikke u-blox modulen du jobber med."""
    
    else:
        return """Jeg kan hjelpe deg med spørsmål om GPS/GNSS-teknologi og u-blox moduler. 

For å gi deg presise svar, last opp relevante brukermanualer eller teknisk dokumentasjon først. Da kan jeg søke i dokumentene og gi deg spesifikke tekniske detaljer."""

@app.get("/documents")
async def list_processed_documents():
    """List alle prosesserte dokumenter i Weaviate"""
    
    if not weaviate_client:
        return {"documents": [], "status": "weaviate_unavailable"}
    
    try:
        documents_collection = weaviate_client.collections.get("Document")
        
        # Get all documents with v4 API
        result = documents_collection.query.fetch_objects(
            limit=1000,
            return_properties=["document_id", "filename"]
        )
        
        # Group by document_id and filename
        documents_dict = {}
        for obj in result.objects:
            doc_id = obj.properties.get("document_id")
            filename = obj.properties.get("filename")
            key = f"{doc_id}|{filename}"
            
            if key not in documents_dict:
                documents_dict[key] = {
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_count": 0
                }
            documents_dict[key]["chunk_count"] += 1
        
        documents = list(documents_dict.values())
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return {"documents": [], "error": str(e)}

@app.delete("/documents/{document_id}")
async def delete_processed_document(document_id: str):
    """Slett et prosessert dokument fra Weaviate"""
    
    if not weaviate_client:
        raise HTTPException(status_code=503, detail="Weaviate ikke tilgjengelig")
    
    try:
        documents_collection = weaviate_client.collections.get("Document")
        
        # Delete all chunks for the document with v4 API
        documents_collection.data.delete_many(
            where=Filter.by_property("document_id").equal(document_id)
        )
        
        return {"message": f"Dokument {document_id} slettet fra RAG-systemet"}
        
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail="Kunne ikke slette dokument")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 
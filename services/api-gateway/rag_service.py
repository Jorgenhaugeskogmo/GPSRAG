"""
GPSRAG Service - Complete RAG Implementation
Håndterer PDF prosessering, embeddings og vector søk
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import re
import tempfile

# CRITICAL: Apply NumPy compatibility patches FIRST
import numpy_compat  # This MUST be first

# RAG Dependencies  
import openai
from pypdf import PdfReader
import numpy as np
import chromadb
# from chromadb.config import Settings # Ikke lenger nødvendig
import tiktoken

logger = logging.getLogger(__name__)

class GPSRAGService:
    def __init__(self):
        """
        Initialiserer RAG service med en in-memory database.
        Denne instansen vil bli delt på tvers av hele applikasjonen.
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.error("❌ OPENAI_API_KEY mangler.")
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Enkel in-memory client
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="gpsrag_shared_in_memory",
            metadata={"hnsw:space": "cosine"}
        )
        self.initialized = True
        logger.info(f"✅ In-memory RAG Service initialisert med collection: {self.collection.name}")
        # self.in_memory_docs er ikke lenger nødvendig, Chroma håndterer det.

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Ekstraherer tekst fra PDF"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text += f"\n--- Side {page_num + 1} ---\n"
                    text += page_text
            
            logger.info(f"✅ Ekstraherte {len(text)} tegn fra PDF")
            return text
            
        except Exception as e:
            logger.error(f"❌ PDF ekstrahering feilet: {e}")
            raise Exception(f"Kunne ikke lese PDF: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Deler tekst opp i chunks med overlap"""
        chunks = []
        
        # Split på paragraphs først
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            # Sjekk om å legge til dette paragraph ville overskride chunk_size
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= chunk_size:
                current_chunk = potential_chunk
            else:
                # Lagre current chunk hvis den ikke er tom
                if current_chunk.strip():
                    chunks.append({
                        "id": f"chunk_{chunk_id}",
                        "text": current_chunk.strip(),
                        "tokens": len(self.tokenizer.encode(current_chunk))
                    })
                    chunk_id += 1
                
                # Start ny chunk med overlap
                if len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Legg til siste chunk
        if current_chunk.strip():
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "text": current_chunk.strip(),
                "tokens": len(self.tokenizer.encode(current_chunk))
            })
        
        logger.info(f"✅ Opprettet {len(chunks)} tekst-chunks")
        return chunks

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Lager embeddings ved å kalle OpenAI API direkte med httpx for å unngå bibliotek-konflikter."""
        try:
            import httpx
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            json_data = {
                "input": texts,
                "model": "text-embedding-ada-002"
            }
            
            logger.info(f"🔄 Kaller OpenAI Embeddings API direkte for {len(texts)} tekstblokker...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=json_data,
                    timeout=30.0
                )
            
            response.raise_for_status() # Sjekker for HTTP-feil (4xx, 5xx)
            
            response_data = response.json()
            embeddings = [item['embedding'] for item in response_data['data']]
            
            logger.info(f"✅ Lagde {len(embeddings)} embeddings via direkte API-kall")
            return embeddings
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP-feil ved direkte kall til OpenAI: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OpenAI API-feil: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Embedding feil (direkte kall): {e}", exc_info=True)
            raise Exception(f"Kunne ikke lage embeddings: {str(e)}")

    async def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Prosesserer dokument komplett - PDF → chunks → embeddings → lagring"""
        try:
            # 1. Ekstraher tekst fra PDF
            text = self.extract_text_from_pdf(file_path)
            
            if not text.strip():
                logger.warning(f"⚠️ Ingen tekst funnet i PDF: {filename}")
                return {
                    "status": "error",
                    "message": "Ingen tekst funnet i dokumentet",
                    "filename": filename
                }
            
            # 2. Del opp i chunks
            chunks = self.chunk_text(text)
            
            if not chunks:
                logger.warning(f"⚠️ Kunne ikke lage chunks fra: {filename}")
                return {
                    "status": "error",
                    "message": "Kunne ikke prosessere dokumentteksten",
                    "filename": filename
                }
            
            # 3. Lag embeddings
            chunk_texts = [chunk["text"] for chunk in chunks]
            try:
                embeddings = await self.create_embeddings(chunk_texts)
            except Exception as e:
                logger.error(f"❌ Embedding feilet: {e}", exc_info=True)
                # Forenklet feilhåndtering - kast unntaket videre
                raise Exception(f"Kunne ikke lage embeddings: {e}")
            
            # 4. Lagre i den delte ChromaDB-instansen
            doc_id = str(uuid.uuid4())
            
            try:
                self._store_in_chromadb(doc_id, filename, chunks, embeddings)
                logger.info(f"✅ Dokument lagret i delt ChromaDB: {filename}")
            except Exception as e:
                logger.error(f"❌ ChromaDB lagring feilet: {e}", exc_info=True)
                raise Exception(f"Kunne ikke lagre i ChromaDB: {e}")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "filename": filename,
                "chunks_count": len(chunks),
                "total_tokens": sum(chunk["tokens"] for chunk in chunks),
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"❌ Dokument prosessering feilet: {e}")
            return {
                "status": "error",
                "message": str(e),
                "filename": filename
            }

    def _store_in_chromadb(self, doc_id: str, filename: str, chunks: List[Dict], embeddings: List[List[float]]):
        """Lagrer dokumentet i ChromaDB"""
        chunk_ids = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_ids.append(f"{doc_id}_chunk_{i}")
            metadatas.append({
                "filename": filename,
                "doc_id": doc_id,
                "chunk_index": i
            })
            documents.append(chunk["text"])
        
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Søker i dokumenter kun med den delte ChromaDB-instansen"""
        try:
            # Lag embedding for query
            query_embeddings = await self.create_embeddings([query])
            query_embedding = query_embeddings[0]
            
            if self.collection is not None:
                # Søk i ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Format resultater
                search_results = []
                if results["documents"] and len(results["documents"][0]) > 0:
                    for i in range(len(results["documents"][0])):
                        result = {
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "relevance_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                            "filename": results["metadatas"][0][i]["filename"],
                            "chunk_index": results["metadatas"][0][i]["chunk_index"]
                        }
                        search_results.append(result)
                
                logger.info(f"✅ ChromaDB: Fant {len(search_results)} relevante chunks")
                return search_results
            
            else:
                logger.warning("⚠️ Ingen ChromaDB collection tilgjengelig for søk.")
                return []
            
        except Exception as e:
            logger.error(f"❌ Søk feilet: {e}", exc_info=True)
            return []

    async def generate_rag_response(self, query: str, max_tokens: int = 500) -> Dict[str, Any]:
        """Generer RAG respons ved å kalle OpenAI Chat API direkte med httpx."""
        try:
            # 1. Søk relevante dokumenter (dette fungerer allerede)
            search_results = await self.search_documents(query, top_k=3)
            
            if not search_results:
                return {
                    "response": "Beklager, jeg fant ingen relevante dokumenter for spørsmålet ditt.",
                    "sources": [],
                    "context_used": False
                }
            
            # 2. Bygg context fra søkeresultater
            context = "\n".join([f"Fra {r['filename']}:\n{r['text']}" for r in search_results])
            sources = [{"filename": r["filename"], "excerpt": r["text"][:150]} for r in search_results]
            
            # 3. Lag prompt
            prompt = f"""Du er en AI-assistent for GPS-teknologi. Svar på spørsmålet kun basert på følgende kontekst.
            
KONTEKST:
{context}

SPØRSMÅL: {query}

SVAR:"""

            # 4. Kall OpenAI Chat API direkte
            import httpx
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            json_data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
            }
            
            logger.info("🤖 Kaller OpenAI Chat API direkte...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=json_data,
                    timeout=45.0
                )
            
            response.raise_for_status()
            
            ai_response = response.json()["choices"][0]["message"]["content"].strip()
            
            logger.info("✅ RAG respons generert via direkte API-kall.")
            
            return {
                "response": ai_response,
                "sources": sources,
                "context_used": True
            }
            
        except Exception as e:
            logger.error(f"❌ RAG respons feil (direkte kall): {e}", exc_info=True)
            return {
                "response": f"Beklager, en teknisk feil oppstod: {str(e)}",
                "sources": [],
                "context_used": False
            }

# Global RAG service er ikke lenger nødvendig, den håndteres av appens livssyklus
# rag_service = None
# def get_rag_service():
# ... (hele funksjonen kan slettes) 
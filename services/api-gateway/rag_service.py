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

# RAG Dependencies
import openai
from pypdf import PdfReader
import numpy as np
import chromadb
from chromadb.config import Settings
import tiktoken

logger = logging.getLogger(__name__)

class GPSRAGService:
    def __init__(self):
        """Initialiserer RAG service"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.error("❌ OPENAI_API_KEY mangler - RAG vil ikke fungere")
            logger.error("🔧 Sett OPENAI_API_KEY i Railway environment variables")
        else:
            logger.info(f"✅ OpenAI API nøkkel funnet (starter med: {self.openai_api_key[:8]}...)")
            
        # OpenAI klient vil bli initialisert når behov
        logger.info("🚀 Initialiserer RAG service...")
        
        # Initialiser ChromaDB (lokal vector database for Railway)
        try:
            # Opprett ChromaDB directory hvis den ikke eksisterer
            chromadb_path = "/tmp/chromadb"
            os.makedirs(chromadb_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chromadb_path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Hent eller opprett collection
            try:
                self.collection = self.chroma_client.get_collection("gpsrag_documents")
                logger.info("✅ Koblet til eksisterende ChromaDB collection")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="gpsrag_documents",
                    metadata={"description": "GPSRAG dokument chunks med embeddings"}
                )
                logger.info("✅ Opprettet ny ChromaDB collection")
        
        except Exception as e:
            logger.error(f"❌ ChromaDB initialisering feilet: {e}")
            self.chroma_client = None
            self.collection = None
            logger.warning("⚠️ Bruker in-memory fallback for embeddings")
        
        # Tiktoken for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

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
        """Lager embeddings med OpenAI v1.40.0 moderne API"""
        try:
            from openai import OpenAI
            
            # Moderne klient - ENKEL versjon
            client = OpenAI(api_key=self.openai_api_key)
            
            logger.info(f"🔄 Lager embeddings for {len(texts)} tekstblokker...")
            
            response = client.embeddings.create(
                input=texts,
                model="text-embedding-ada-002"
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Lagde {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Embedding feil: {e}")
            import traceback
            logger.error(f"📊 Embedding traceback: {traceback.format_exc()}")
            raise Exception(f"Kunne ikke lage embeddings: {str(e)}")

    async def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Prosesserer dokument komplett - PDF → chunks → embeddings → lagring"""
        try:
            # 1. Ekstraher tekst fra PDF
            text = self.extract_text_from_pdf(file_path)
            
            if not text.strip():
                raise Exception("PDF inneholder ingen tekst")
            
            # 2. Del opp i chunks
            chunks = self.chunk_text(text)
            
            if not chunks:
                raise Exception("Kunne ikke lage chunks fra tekst")
            
            # 3. Lag embeddings
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.create_embeddings(chunk_texts)
            
            # 4. Lagre i ChromaDB
            doc_id = str(uuid.uuid4())
            chunk_ids = []
            metadatas = []
            documents = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                metadata = {
                    "filename": filename,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "tokens": chunk["tokens"],
                    "text_length": len(chunk["text"])
                }
                metadatas.append(metadata)
                documents.append(chunk["text"])
            
            # Lagre i ChromaDB hvis tilgjengelig
            if self.collection is not None:
                self.collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                logger.info(f"✅ Dokument lagret i ChromaDB: {filename}")
            else:
                logger.warning("⚠️ ChromaDB ikke tilgjengelig - dokumenter lagres ikke persistent")
            
            logger.info(f"✅ Dokument prosessert: {filename} → {len(chunks)} chunks lagret")
            
            return {
                "doc_id": doc_id,
                "filename": filename,
                "chunks_count": len(chunks),
                "total_tokens": sum(chunk["tokens"] for chunk in chunks),
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"❌ Dokument prosessering feilet: {e}")
            raise

    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Søker i dokumenter med RAG"""
        try:
            if self.collection is None:
                logger.warning("⚠️ ChromaDB ikke tilgjengelig - kan ikke søke i dokumenter")
                return []
            
            # Lag embedding for query
            query_embeddings = await self.create_embeddings([query])
            query_embedding = query_embeddings[0]
            
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
            
            logger.info(f"✅ Fant {len(search_results)} relevante chunks for query")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Søk feilet: {e}")
            return []

    async def generate_rag_response(self, query: str, max_tokens: int = 500) -> Dict[str, Any]:
        """Generer RAG respons med OpenAI"""
        try:
            # 1. Søk relevante dokumenter
            search_results = await self.search_documents(query, top_k=3)
            
            if not search_results:
                return {
                    "response": "Beklager, jeg fant ingen relevante dokumenter for spørsmålet ditt. Last opp noen PDF-er først!",
                    "sources": [],
                    "context_used": False
                }
            
            # 2. Bygg context fra søkeresultater
            context_parts = []
            sources = []
            
            for result in search_results:
                context_parts.append(f"Fra {result['filename']} (relevans: {result['relevance_score']:.2f}):\n{result['text']}\n")
                sources.append({
                    "filename": result["filename"],
                    "relevance_score": result["relevance_score"],
                    "excerpt": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
                })
            
            context = "\n".join(context_parts)
            
            # 3. Lag prompt
            prompt = f"""Du er en AI-assistent som spesialiserer seg på GPS-teknologi og u-blox moduler. Bruk kun informasjonen fra de oppgitte dokumentene til å svare på spørsmålet.

KONTEKST FRA DOKUMENTER:
{context}

SPØRSMÅL: {query}

INSTRUKSJONER:
- Svar kun basert på informasjonen i dokumentene over
- Hvis informasjonen ikke finnes i dokumentene, si det tydelig
- Vær spesifikk og teknisk korrekt
- Referer til relevante dokumenter når mulig
- Svar på norsk

SVAR:"""

            # 4. Kall OpenAI
            from openai import OpenAI
            
            # Moderne klient - ENKEL versjon
            client = OpenAI(api_key=self.openai_api_key)
            
            logger.info(f"🤖 Sender query til OpenAI med {len(context)} tegn context...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du er en ekspert på GPS-teknologi og u-blox moduler. Svar alltid på norsk og bruk kun informasjonen fra de oppgitte dokumentene."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            logger.info(f"✅ RAG respons generert ({len(ai_response)} tegn)")
            
            return {
                "response": ai_response,
                "sources": sources,
                "context_used": True,
                "search_results_count": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"❌ RAG respons feil: {e}")
            return {
                "response": f"Beklager, det oppstod en teknisk feil under prosessering: {str(e)}",
                "sources": [],
                "context_used": False
            }

# Global RAG service instance - lazy initialization for Railway
rag_service = None

def get_rag_service():
    """Lazy initialization av RAG service for Railway deployment"""
    global rag_service
    if rag_service is None:
        try:
            rag_service = GPSRAGService()
            logger.info("✅ RAG service initialisert")
        except Exception as e:
            logger.error(f"❌ RAG service initialisering feilet: {e}")
            # Returner en dummy service som feiler gracefully
            class DummyRAGService:
                async def process_document(self, *args, **kwargs):
                    raise Exception(f"RAG service ikke tilgjengelig: {e}")
                async def generate_rag_response(self, *args, **kwargs):
                    return {
                        "response": f"RAG service ikke tilgjengelig: {e}",
                        "sources": [],
                        "context_used": False
                    }
            rag_service = DummyRAGService()
    return rag_service 
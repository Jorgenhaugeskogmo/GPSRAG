from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import weaviate
from weaviate.auth import AuthApiKey
import openai
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

# --- FastAPI App ---
app = FastAPI(title="GPSRAG Chat API")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = app # For Vercel

# --- Weaviate and OpenAI Setup ---
weaviate_client = None
openai_client = None
init_error = None

try:
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")
    WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not all([WEAVIATE_URL, WEAVIATE_API_KEY, OPENAI_API_KEY]):
        raise ValueError("Mangler nødvendige miljøvariabler: WEAVIATE_URL, WEAVIATE_API_KEY, OPENAI_API_KEY")

    # Fikser URL hvis den mangler scheme
    if not WEAVIATE_URL.startswith(('http://', 'https://')):
        WEAVIATE_URL = 'https://' + WEAVIATE_URL
        logger.info(f"Lagt til https:// prefiks til Weaviate URL: {WEAVIATE_URL}")

    # Opprett Weaviate v4 client
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=AuthApiKey(WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
    )

    # Opprett OpenAI client
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    logger.info("✅ Weaviate og OpenAI clients initialisert vellykket.")

except Exception as e:
    init_error = str(e)
    logger.error(f"❌ Feil under initialisering: {init_error}")


def search_documents(query: str, k: int = 5):
    """Søk i Weaviate for relevante dokumenter"""
    try:
        collection = weaviate_client.collections.get("Ublox_docs")
        
        # Hybrid search med både semantic og keyword
        response = collection.query.hybrid(
            query=query,
            limit=k,
            alpha=0.5  # Balanse mellom semantic og keyword search
        )
        
        documents = []
        for obj in response.objects:
            documents.append({
                "content": obj.properties.get("content", ""),
                "metadata": obj.properties
            })
        
        return documents
    except Exception as e:
        logger.error(f"Feil under søk: {e}")
        return []


def generate_response(query: str, context_docs: list):
    """Generer svar med OpenAI basert på kontekst"""
    try:
        # Bygg kontekst fra dokumenter
        context = "\n\n".join([doc["content"] for doc in context_docs])
        
        # Lag prompt
        system_prompt = """Du er en ekspert på GPS og u-blox-teknologi. Svar på spørsmålet kun basert på følgende kontekst. 
        Hvis informasjonen ikke finnes i konteksten, si det tydelig."""
        
        user_prompt = f"""Kontekst:
{context}

Spørsmål: {query}"""

        # Kall OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Feil under OpenAI kall: {e}")
        raise


# --- API Endpoints ---
@app.post("/")
async def chat_handler(request: ChatRequest):
    if weaviate_client is None or openai_client is None:
        logger.error(f"Forsøkte å kjøre chat, men clients er ikke initialisert. Feil: {init_error}")
        raise HTTPException(status_code=500, detail=f"Client initialization failed: {init_error}")

    try:
        query = request.message
        logger.info(f"Mottok spørsmål: {query}")
        
        # Søk etter relevante dokumenter
        documents = search_documents(query, k=5)
        
        if not documents:
            return JSONResponse(content={
                "response": "Beklager, jeg fant ingen relevante dokumenter for spørsmålet ditt.",
                "sources": []
            })
        
        # Generer svar
        response_text = generate_response(query, documents)
        logger.info(f"Genererte svar: {response_text[:100]}...")

        # Lag kilder
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            sources.append({
                "filename": metadata.get("filename", "Ukjent fil"),
                "excerpt": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "page": metadata.get("page"),
                "relevance_score": metadata.get("score", 0)
            })

        return JSONResponse(content={"response": response_text, "sources": sources})

    except Exception as e:
        logger.error(f"❌ Feil under chat-behandling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    if init_error:
        return {"status": "unhealthy", "error": init_error}
    return {"status": "healthy", "clients_ready": weaviate_client is not None and openai_client is not None}

@app.get("/")
def root():
    return {"message": "GPSRAG API (Chat) er live med minimal dependencies."} 
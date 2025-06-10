from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import weaviate
from weaviate.auth import AuthApiKey
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_weaviate import WeaviateVectorStore
from langchain_openai import OpenAIEmbeddings
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
rag_chain = None
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

    # Opprett embeddings og vector store
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    # Bruk LangChain Weaviate integration
    vectorstore = WeaviateVectorStore(
        client=weaviate_client,
        index_name="Ublox_docs",
        text_key="content",
        embedding=embeddings
    )

    # Opprett retriever
    retriever = vectorstore.as_retriever(
        search_type="hybrid",
        search_kwargs={"k": 5, "alpha": 0.5}
    )

    template = """Du er en ekspert på GPS og u-blox-teknologi. Svar på spørsmålet kun basert på følgende kontekst:
    {context}

    Spørsmål: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=OPENAI_API_KEY)

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    logger.info("✅ RAG chain initialisert vellykket med Weaviate v4.")

except Exception as e:
    init_error = str(e)
    logger.error(f"❌ Feil under initialisering av RAG chain: {init_error}")


# --- API Endpoints ---
@app.post("/")
async def chat_handler(request: ChatRequest):
    if rag_chain is None:
        logger.error(f"Forsøkte å kjøre chat, men RAG chain er ikke initialisert. Feil: {init_error}")
        raise HTTPException(status_code=500, detail=f"RAG chain initialization failed: {init_error}")

    try:
        query = request.message
        logger.info(f"Mottok spørsmål: {query}")
        
        # Her henter vi kildene FØR vi kaller kjeden
        source_documents = retriever.get_relevant_documents(query)
        
        response_text = rag_chain.invoke(query)
        logger.info(f"Genererte svar: {response_text[:100]}...")

        sources = []
        for doc in source_documents:
            # Weaviate kan returnere metadata litt annerledes
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            sources.append({
                "filename": metadata.get("filename", "Ukjent fil"),
                "excerpt": doc.page_content,
                # Disse er ikke alltid tilgjengelig, så vi bruker get med default
                "page": metadata.get("page"),
                "relevance_score": metadata.get("_additional", {}).get("score", 0)
            })

        return JSONResponse(content={"response": response_text, "sources": sources})

    except Exception as e:
        logger.error(f"❌ Feil under chat-behandling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    if init_error:
        return {"status": "unhealthy", "error": init_error}
    return {"status": "healthy", "rag_enabled": rag_chain is not None}

@app.get("/")
def root():
    return {"message": "GPSRAG API (Chat) er live."} 
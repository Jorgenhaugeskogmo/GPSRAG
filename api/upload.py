from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import weaviate
from weaviate.auth import AuthApiKey
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# --- CORS Middleware ---
# Tillater frontend (kjører på Vercel) å kommunisere med denne API-funksjonen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tillater alle origins
    allow_credentials=True,
    allow_methods=["*"],  # Tillater alle metoder
    allow_headers=["*"],  # Tillater alle headers
)

# Dette er Vercel sin måte å wrappe FastAPI
# Se: https://vercel.com/docs/functions/serverless-functions/runtimes/python
handler = app 

@app.post("/")
async def upload_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Mottok fil: {file.filename}")

        # Lagre filen midlertidig
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Fil lagret midlertidig på: {tmp_file_path}")

        # Hent miljøvariabler
        WEAVIATE_URL = os.getenv("WEAVIATE_URL")
        WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if not all([WEAVIATE_URL, WEAVIATE_API_KEY, OPENAI_API_KEY]):
            logger.error("Mangler miljøvariabler")
            raise ValueError("Missing environment variables")

        # Fikser URL hvis den mangler scheme
        if not WEAVIATE_URL.startswith(('http://', 'https://')):
            WEAVIATE_URL = 'https://' + WEAVIATE_URL
            logger.info(f"Lagt til https:// prefiks til Weaviate URL: {WEAVIATE_URL}")

        # Koble til Weaviate v4
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=AuthApiKey(WEAVIATE_API_KEY),
            headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
        )
        logger.info("Koblet til Weaviate v4")

        # Last og splitt dokumentet
        loader = PyPDFLoader(tmp_file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        logger.info(f"Dokument splittet i {len(docs)} deler")

        # Last opp til Weaviate v4
        collection = client.collections.get("Ublox_docs")
        objects_to_insert = []
        
        for i, doc in enumerate(docs):
            objects_to_insert.append({
                "content": doc.page_content,
                "filename": file.filename,
                "page": doc.metadata.get("page", 0) + 1,
            })
        
        # Batch insert med v4 API
        result = collection.data.insert_many(objects_to_insert)
        logger.info(f"Data lastet opp til Weaviate v4: {len(objects_to_insert)} objekter")

        # Lukk klient og slett temp fil
        client.close()
        os.remove(tmp_file_path)
        
        return JSONResponse(
            status_code=200,
            content={'message': f'Successfully processed and stored {len(docs)} chunks from {file.filename}.'}
        )

    except Exception as e:
        logger.error(f"En feil oppstod under filopplasting: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={'error': f"An error occurred: {str(e)}"}
        ) 
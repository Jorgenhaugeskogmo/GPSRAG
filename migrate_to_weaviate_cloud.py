"""
Script for å migrere lokal Weaviate data til Weaviate Cloud
for Vercel deployment
"""

import weaviate
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Hent OpenAI API-nøkkel
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set!")

# Local Weaviate
LOCAL_WEAVIATE_URL = "http://localhost:8080"

# Weaviate Cloud - disse må settes som environment variabler
WEAVIATE_CLOUD_URL = os.getenv("WEAVIATE_CLOUD_URL")
WEAVIATE_CLOUD_API_KEY = os.getenv("WEAVIATE_CLOUD_API_KEY")
if not WEAVIATE_CLOUD_URL or not WEAVIATE_CLOUD_API_KEY:
    raise ValueError("WEAVIATE_CLOUD_URL or WEAVIATE_CLOUD_API_KEY environment variable not set!")

def export_local_data():
    """Export data from local Weaviate"""
    try:
        client = weaviate.Client(LOCAL_WEAVIATE_URL)
        
        # Query all documents, with a high limit to get all of them
        query = """
        {
            Get {
                Document(limit: 5000) {
                    content
                    filename
                    chunk_index
                    document_id
                    created_at
                    metadata
                }
            }
        }
        """
        
        result = client.query.raw(query)
        documents = result.get("data", {}).get("Get", {}).get("Document", [])
        
        print(f"Exported {len(documents)} documents from local Weaviate")
        return documents
        
    except Exception as e:
        print(f"Error exporting local data: {e}")
        return []

def import_to_cloud(documents):
    """Import data to Weaviate Cloud"""
    try:
        auth_config = weaviate.AuthApiKey(api_key=WEAVIATE_CLOUD_API_KEY)
        client = weaviate.Client(
            url=WEAVIATE_CLOUD_URL,
            auth_client_secret=auth_config,
            additional_headers={
                "X-OpenAI-Api-Key": OPENAI_API_KEY
            }
        )
        
        # Create schema
        schema = {
            "class": "Document",
            "description": "GPS/u-blox documentation chunks",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "filename", 
                    "dataType": ["string"],
                    "description": "Source filename"
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "Chunk index in document"
                },
                {
                    "name": "document_id",
                    "dataType": ["string"],
                    "description": "Document ID"
                },
                {
                    "name": "created_at",
                    "dataType": ["string"],
                    "description": "Creation timestamp"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Additional metadata"
                }
            ],
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            }
        }
        
        # Create class if it doesn't exist
        try:
            # First, check if the class exists
            schema_json = client.schema.get("Document")
            print("Document class already exists.")
            
            # Optional: Delete existing class if you want to start fresh
            # client.schema.delete_class("Document")
            # print("Deleted existing Document class.")
            # client.schema.create_class(schema)
            # print("Re-created Document class in Weaviate Cloud")

        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if e.status_code == 404:
                 # Class does not exist, create it
                client.schema.create_class(schema)
                print("Created Document class in Weaviate Cloud")
            else:
                # Some other error occurred
                raise e
        
        # Import documents
        with client.batch(
            batch_size=100,
            num_workers=2
        ) as batch:
            for i, doc in enumerate(documents):
                try:
                    # Ensure metadata is a string, handle if it's None or a dict
                    if isinstance(doc.get('metadata'), dict):
                        doc['metadata'] = json.dumps(doc['metadata'])
                    elif doc.get('metadata') is None:
                        doc['metadata'] = "{}"

                    batch.add_data_object(
                        data_object=doc,
                        class_name="Document"
                    )
                    
                    if (i + 1) % 100 == 0:
                        print(f"Added {i+1}/{len(documents)} documents to the batch")
                        
                except Exception as e:
                    print(f"Error adding document {i} to batch: {e}")
        
        print(f"Successfully added {len(documents)} documents to the batch. The import is now running in the background.")
        return True
        
    except Exception as e:
        print(f"Error importing to cloud: {e}")
        return False

def main():
    print("Starting migration from local Weaviate to Weaviate Cloud...")
    
    # Export from local
    documents = export_local_data()
    
    if not documents:
        print("No documents found to migrate")
        return
    
    # Import to cloud
    success = import_to_cloud(documents)
    
    if success:
        print("Migration completed successfully!")
        print(f"Weaviate Cloud URL: {WEAVIATE_CLOUD_URL}")
        print("Set WEAVIATE_CLOUD_URL and WEAVIATE_CLOUD_API_KEY as Vercel environment variables")
    else:
        print("Migration failed")

if __name__ == "__main__":
    main() 
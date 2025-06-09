# GPSRAG Prosjektstruktur

## 📁 Komplett Filstruktur

```
GPSRAG/
├── 📄 README.md                          # Hovedprosjekt dokumentasjon
├── 📄 ARCHITECTURE.md                    # Detaljert arkitekturdokumentasjon  
├── 📄 CONTRIBUTING.md                    # Bidragsinstruksjoner for utviklere
├── 📄 PROJECT_STRUCTURE.md               # Denne filen - prosjektoversikt
├── 📄 docker-compose.yml                 # Hovedkonfigurasjon for alle tjenester
├── 📄 env.example                        # Eksempel på miljøvariabler
├── 📄 requirements.txt                   # Python avhengigheter (rot-nivå)
│
├── 📁 frontend/                          # React/Next.js frontend applikasjon
│   ├── 📄 package.json                   # Node.js avhengigheter og scripts
│   ├── 📄 next.config.js                 # Next.js konfigurasjon
│   ├── 📄 tailwind.config.js             # Tailwind CSS konfigurasjon
│   ├── 📄 Dockerfile                     # Container konfigurasjon
│   ├── 📁 pages/                         # Next.js sider
│   │   ├── 📄 _app.tsx                   # Global applikasjonskonfigurasjon
│   │   └── 📄 index.tsx                  # Hovedside med tab-navigasjon
│   ├── 📁 components/                    # React komponenter
│   │   ├── 📁 layout/
│   │   │   └── 📄 Layout.tsx             # Hovedlayout komponent
│   │   ├── 📁 chat/
│   │   │   └── 📄 ChatInterface.tsx      # Chat grensesnitt komponent
│   │   ├── 📁 upload/
│   │   │   └── 📄 DocumentUpload.tsx     # Fil upload komponent
│   │   └── 📁 visualization/
│   │       └── 📄 GPSVisualization.tsx   # GPS visualisering komponent
│   ├── 📁 styles/
│   │   └── 📄 globals.css                # Global CSS med Tailwind
│   ├── 📁 hooks/                         # Custom React hooks
│   ├── 📁 lib/                          # Utility biblioteker
│   └── 📁 types/                        # TypeScript type definisjoner
│
├── 📁 services/                          # Mikroservice backend tjenester
│   ├── 📁 api-gateway/                   # Hovedport - API Gateway (Port 8000)
│   │   ├── 📄 main.py                    # FastAPI applikasjon entry point
│   │   ├── 📄 requirements.txt           # Python avhengigheter
│   │   ├── 📄 Dockerfile                 # Container konfigurasjon
│   │   ├── 📁 src/                       # Kildekode
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py              # Applikasjonskonfigurasjon
│   │   │   ├── 📄 database.py            # Database modeller og tilkobling
│   │   │   ├── 📁 routers/               # API endepunkter
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 auth.py            # Autentisering API
│   │   │   │   ├── 📄 chat.py            # Chat API med RAG-integrasjon
│   │   │   │   ├── 📄 documents.py       # Dokument upload API
│   │   │   │   ├── 📄 gps.py             # GPS data API
│   │   │   │   ├── 📄 health.py          # Helse-sjekk endepunkter
│   │   │   │   └── 📄 visualizations.py  # Visualisering API
│   │   │   ├── 📁 schemas/               # Pydantic schemas
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   └── 📄 chat.py            # Chat API schemas
│   │   │   ├── 📁 services/              # Business logic tjenester
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   └── 📄 websocket_manager.py # WebSocket håndtering
│   │   │   └── 📁 models/                # Database modeller (alternative)
│   │   │       └── 📄 __init__.py
│   │   └── 📁 tests/                     # Enhetstester
│   │       └── 📄 __init__.py
│   │
│   ├── 📁 ingestion/                     # PDF og data-ingest tjeneste (Port 8001)
│   │   ├── 📁 src/                       # Kildekode for ingest
│   │   └── 📁 tests/                     # Ingest tester
│   │
│   ├── 📁 rag-engine/                    # LangChain RAG-motor (Port 8002)
│   │   ├── 📁 src/                       # RAG implementasjon
│   │   └── 📁 tests/                     # RAG tester
│   │
│   ├── 📁 visualization/                 # Graf-generering tjeneste (Port 8003)
│   │   ├── 📁 src/                       # Visualisering logikk
│   │   └── 📁 tests/                     # Visualisering tester
│   │
│   └── 📁 mlops/                         # ML pipeline og trening (Port 8004)
│       ├── 📁 dags/                      # Airflow DAG-er
│       │   └── 📄 gps_training_pipeline.py # ML trening pipeline
│       ├── 📁 plugins/                   # Airflow plugins
│       └── 📁 tests/                     # MLOps tester
│
├── 📁 infrastructure/                    # Infrastruktur og deployment
│   ├── 📁 docker/                        # Docker-spesifikke filer
│   │   ├── 📁 postgres/                  # Database konfigurasjon
│   │   │   └── 📄 init.sql               # Database initialisering
│   │   └── 📁 grafana/                   # Monitoring konfigurasjon
│   │       └── 📁 dashboards/            # Grafana dashboards
│   └── 📁 k8s/                          # Kubernetes manifester (produksjon)
│
├── 📁 data/                              # Lokal data storage
│   ├── 📁 uploads/                       # Opplastede filer
│   ├── 📁 processed/                     # Behandlede data
│   └── 📁 models/                        # Lagrede ML-modeller
│
└── 📁 scripts/                           # Utility scripts
    ├── 📄 setup.sh                       # Automatisk oppsett av utviklingsmiljø
    └── 📄 run-tests.sh                   # Kjør alle tester
```

## 🎯 Tjenesteportoversikt

### Hovedtjenester
- **Frontend**: http://localhost:3000 - React/Next.js brukergrensesnitt
- **API Gateway**: http://localhost:8000 - Hovedport for alle API-kall
- **API Docs**: http://localhost:8000/docs - Swagger/OpenAPI dokumentasjon

### Infrastrukturtjenester  
- **PostgreSQL**: localhost:5432 - Hoveddatabase for metadata
- **Weaviate**: http://localhost:8080 - Vektor-database for embeddings
- **Redis**: localhost:6379 - Cache og task queue
- **MinIO**: http://localhost:9000 - Objekt-storage (S3-kompatibel)

### MLOps og Monitoring
- **Airflow**: http://localhost:8081 - ML pipeline orkestrasjon
- **Grafana**: http://localhost:3001 - Monitoring og dashboards

## 🚀 Rask Start

### 1. Initial Setup
```bash
# Klon repositoriet
git clone <repository-url>
cd GPSRAG

# Kjør automatisk oppsett
./scripts/setup.sh
```

### 2. Start Alle Tjenester
```bash
# Start alle tjenester i bakgrunnen
docker-compose up -d

# Se status på tjenester
docker-compose ps

# Følg logger for alle tjenester
docker-compose logs -f
```

### 3. Utvikling
```bash
# Start kun infrastruktur (for lokal utvikling)
docker-compose up -d postgres weaviate redis minio

# Start backend lokalt
cd services/api-gateway
source ../../venv/bin/activate
uvicorn main:app --reload

# Start frontend lokalt (i ny terminal)
cd frontend
npm run dev
```

### 4. Testing
```bash
# Kjør alle tester
./scripts/run-tests.sh

# Eller kjør spesifikke tester
cd services/api-gateway && pytest
cd frontend && npm test
```

## 📊 Arkitektur Sammendrag

### Microservice Design
- **API Gateway**: Hovedinngangspunkt, autentisering, routing
- **Ingestion Service**: PDF og GPS-data behandling
- **RAG Engine**: LangChain-basert spørsmål-svar system
- **Visualization Service**: Graf og kart generering
- **MLOps Service**: Automatisk ML-pipeline med Airflow

### Data Flow
1. **Document Upload** → Ingestion → Vector DB → RAG retrieval
2. **GPS Data** → Processing → PostgreSQL → Visualization
3. **User Query** → RAG Engine → Context + LLM → Response
4. **ML Training** → Airflow → Feature Engineering → Model Training → Deployment

### Technology Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, SQLAlchemy, Pydantic
- **AI/ML**: LangChain, OpenAI, Weaviate, scikit-learn
- **Data**: PostgreSQL, Redis, MinIO, Weaviate
- **DevOps**: Docker, Docker Compose, Airflow, Grafana

Dette prosjektet gir en komplett, produktionsklar foundation for en RAG-drevet GPS-analyseapplikasjon som kan skaleres og utvides etter behov. 
# GPSRAG - GPS Document Analysis System

System for analyse av GPS-relaterte dokumenter ved hjelp av AI og RAG (Retrieval-Augmented Generation).

## Deployment Status
Sist oppdatert: Nå med riktige API URLs for Railway deployment

## Services
- Frontend: Next.js applikasjon
- API Gateway: HovedAPI for all kommunikasjon  
- RAG Engine: AI-basert dokumentanalyse
- Document Service: Håndtering av dokumentopplasting
- Vector Database: Weaviate for embeddings
- PostgreSQL: Hoveddatabase
- Redis: Cache og session storage

## Live URL
https://gpsrag-production.up.railway.app

## 🏗️ Arkitektur Oversikt

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chat Frontend │    │   API Gateway   │    │ Ingestion Svc   │
│   (React+TW)    │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Visualization   │    │   RAG Engine    │    │   Vector DB     │
│   Service       │◄──►│  (LangChain)    │◄──►│  (Weaviate)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MLOps Pipeline│    │   Metadata DB   │    │   File Storage  │
│   (Airflow)     │    │  (PostgreSQL)   │    │   (MinIO/S3)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Rask Start

```bash
# Klon prosjektet
git clone <repository-url>
cd GPSRAG

# Start alle tjenester
docker compose up -d

# Tilgang til applikasjonen
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Weaviate: http://localhost:8080
# Airflow: http://localhost:8080/airflow
```

## 📁 Prosjektstruktur

```
GPSRAG/
├── frontend/                 # React chatapplikasjon
├── services/
│   ├── api-gateway/         # FastAPI gateway
│   ├── ingestion/           # PDF og data-ingest
│   ├── rag-engine/          # LangChain RAG-motor
│   ├── visualization/       # Graf-generering
│   └── mlops/              # ML pipeline og trening
├── infrastructure/
│   ├── docker/             # Docker-konfigurasjon
│   └── k8s/               # Kubernetes manifester
├── data/                   # Lokal data storage
└── scripts/               # Utility scripts
```

## 🛠️ Teknologi Stack

- **Frontend**: React 18 + TypeScript + Tailwind CSS + Chart.js
- **Backend**: FastAPI + Python 3.11
- **RAG**: LangChain + OpenAI/Ollama + Weaviate
- **Database**: PostgreSQL + Weaviate (vektor)
- **MLOps**: Apache Airflow + MLflow
- **DevOps**: Docker + Docker Compose + GitHub Actions

## 📋 Funksjonalitet

### ✅ Kjernefunksjoner
- PDF-opplasting og tekstekstraksjon
- Vektor-embedding og søk
- Interaktiv chat med RAG
- GPS-data visualisering
- Historisk dataanalyse

### 🔮 Planlagte Funksjoner
- Batch ML-trening
- Prediktive modeller
- Sanntids GPS-sporing
- Multi-tenant support

## 🔧 Utvikling

### Forutsetninger
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Cursor IDE (anbefalt)

### Lokal Utvikling
```bash
# Backend utvikling
cd services/api-gateway
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend utvikling
cd frontend
npm install
npm run dev
```

## 📊 Monitorering
- Grafana dashboards: http://localhost:3001
- Prometheus metrics: http://localhost:9090
- Application logs: `docker compose logs -f`

## 🧪 Testing
```bash
# Kjør alle tester
./scripts/run-tests.sh

# Spesifikke tester
pytest services/api-gateway/tests/
npm test --prefix frontend
```

## 📝 API Dokumentasjon
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Bidrag
Se [CONTRIBUTING.md](CONTRIBUTING.md) for retningslinjer.

## 📄 Lisens
MIT License - Se [LICENSE](LICENSE) for detaljer. 
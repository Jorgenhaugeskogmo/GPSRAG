#!/bin/bash

# GPSRAG Setup Script
# Setter opp utviklingsmiljø for GPSRAG-prosjektet

set -e

echo "🚀 Setter opp GPSRAG utviklingsmiljø..."

# Sjekk forutsetninger
echo "📋 Sjekker forutsetninger..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker er ikke installert. Installer Docker først."
    exit 1
fi

# Sjekk for Docker Compose (både ny og gammel syntaks)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose er ikke installert. Installer Docker Compose først."
    exit 1
fi

# Bestem hvilken Docker Compose kommando som skal brukes
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 er ikke installert."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js er ikke installert."
    exit 1
fi

echo "✅ Alle forutsetninger oppfylt"

# Lag miljøvariabler
echo "📝 Setter opp miljøvariabler..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ .env fil opprettet fra env.example"
    echo "⚠️  Husk å oppdatere API-nøkler i .env-filen"
else
    echo "✅ .env fil eksisterer allerede"
fi

# Opprett nødvendige mapper
echo "📁 Oppretter mapper..."
mkdir -p data/{uploads,processed,models}
mkdir -p logs
echo "✅ Mapper opprettet"

# Installer Python-avhengigheter for lokal utvikling
echo "🐍 Installerer Python-avhengigheter..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r services/api-gateway/requirements.txt
    echo "✅ Python-avhengigheter installert"
else
    echo "⚠️  Virtuelt miljø ikke funnet. Kjør 'python3 -m venv venv' først."
fi

# Installer Node.js-avhengigheter
echo "📦 Installerer Node.js-avhengigheter..."
cd frontend
if [ -f "package.json" ]; then
    npm install
    echo "✅ Node.js-avhengigheter installert"
    cd ..
else
    echo "❌ package.json ikke funnet i frontend-mappen"
    cd ..
    exit 1
fi

# Bygg Docker-images
echo "🐳 Bygger Docker-images..."
$DOCKER_COMPOSE build --no-cache

echo "✅ Setup fullført!"
echo ""
echo "🎉 GPSRAG er nå klar til bruk!"
echo ""
echo "For å starte applikasjonen, kjør:"
echo "  $DOCKER_COMPOSE up -d"
echo ""
echo "For å se status:"
echo "  $DOCKER_COMPOSE ps"
echo ""
echo "For å se logger:"
echo "  $DOCKER_COMPOSE logs -f"
echo ""
echo "Tilgang til tjenester:"
echo "  - Frontend: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Weaviate: http://localhost:8080"
echo "  - Airflow: http://localhost:8081"
echo "  - Grafana: http://localhost:3001" 
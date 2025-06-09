#!/bin/bash

# GPSRAG Deployment Script
# Dette scriptet hjelper deg med å deployere GPSRAG til forskjellige platformer

echo "🚀 GPSRAG Deployment Helper"
echo "========================================="

# Sjekk om git er initialisert
if [ ! -d ".git" ]; then
    echo "❗ Git repository er ikke initialisert. Initialiserer nå..."
    git init
    git add .
    git commit -m "Initial commit for GPSRAG deployment"
fi

echo ""
echo "Velg deployment platform:"
echo "1) Railway (Anbefalt for testing - Gratis tier)"
echo "2) DigitalOcean App Platform"
echo "3) VPS med Docker"
echo "4) Lokal produksjonstesting"
echo ""

read -p "Velg alternativ (1-4): " choice

case $choice in
    1)
        echo "🚄 Railway Deployment"
        echo "====================="
        
        # Sjekk om Railway CLI er installert
        if ! command -v railway &> /dev/null; then
            echo "📦 Installerer Railway CLI..."
            npm install -g @railway/cli
        fi
        
        echo "🔐 Logger inn på Railway..."
        railway login
        
        echo "🎯 Initialiserer Railway prosjekt..."
        railway init
        
        echo "📤 Deployer til Railway..."
        railway up
        
        echo "✅ Deployment ferdig!"
        echo "📱 Din app vil være tilgjengelig på en URL som Railway gir deg"
        echo "🔧 Husk å legge til miljøvariabler i Railway dashboard:"
        echo "   - OPENAI_API_KEY"
        echo "   - DATABASE_URL (opprett PostgreSQL service)"
        echo "   - REDIS_URL (opprett Redis service)"
        ;;
        
    2)
        echo "🌊 DigitalOcean App Platform"
        echo "=========================="
        
        echo "📋 For å deployere til DigitalOcean App Platform:"
        echo "1. Push koden til GitHub:"
        echo "   git remote add origin https://github.com/your-username/GPSRAG.git"
        echo "   git push -u origin main"
        echo ""
        echo "2. Gå til https://cloud.digitalocean.com/apps"
        echo "3. Klikk 'Create App'"
        echo "4. Velg 'GitHub' og koble til repo"
        echo "5. DigitalOcean vil automatisk oppdage Docker setup"
        echo "6. Legg til miljøvariabler i App settings"
        echo ""
        echo "💰 Estimert kostnad: $50-100/måned"
        ;;
        
    3)
        echo "🖥️  VPS Deployment"
        echo "=================="
        
        read -p "Server IP adresse: " server_ip
        read -p "SSH brukernavn (ubuntu): " ssh_user
        ssh_user=${ssh_user:-ubuntu}
        
        echo "📤 Kopierer filer til server..."
        rsync -avz --exclude '.git' --exclude 'node_modules' . $ssh_user@$server_ip:~/GPSRAG/
        
        echo "🐳 Setter opp Docker på server..."
        ssh $ssh_user@$server_ip << 'EOF'
            sudo apt update
            sudo apt install -y docker.io docker-compose-plugin
            cd ~/GPSRAG
            cp env.example .env
            echo "✏️  Rediger .env filen med produksjonsinnstillinger"
            nano .env
            sudo docker compose -f docker-compose.prod.yml up -d
EOF
        
        echo "✅ Deployment ferdig!"
        echo "🌐 Din app er tilgjengelig på http://$server_ip"
        ;;
        
    4)
        echo "🧪 Lokal produksjonstesting"
        echo "========================="
        
        echo "📝 Kopierer miljøfil..."
        cp env.example .env.prod
        
        echo "🐳 Bygger og starter produksjonscontainere..."
        docker compose -f docker-compose.prod.yml build
        docker compose -f docker-compose.prod.yml up -d
        
        echo "✅ Produksjonstest startet!"
        echo "🌐 Test applikasjonen på http://localhost"
        echo "🔧 For å stoppe: docker compose -f docker-compose.prod.yml down"
        ;;
        
    *)
        echo "❌ Ugyldig valg. Prøv igjen."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment prosess ferdig!"
echo "📚 Se deploy/README.md for detaljerte instruksjoner"
echo "🆘 Trenger du hjelp? Kontakt utviklerteamet" 
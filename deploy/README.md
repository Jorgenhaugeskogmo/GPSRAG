# 🚀 GPSRAG Deployment Guide

## Deployment-alternativer

### 1. DigitalOcean App Platform (Anbefalt - Enklest)

**Fordeler:**
- Automatisk skalering
- Integrert database og Redis
- SSL-sertifikater inkludert
- Ca. $50-100/måned for team

**Deploy steg:**

1. **Push koden til GitHub**
2. **Opprett DigitalOcean konto**
3. **Opprett ny App i DigitalOcean**
4. **Koble til GitHub repo**
5. **Konfigurer miljøvariabler**

### 2. Railway (Svært enkelt)

**Fordeler:**
- Gratis tier tilgjengelig
- Automatisk deployment fra GitHub
- Integrert database
- Perfekt for testing

**Deploy kommando:**
```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login og deploy
railway login
railway link
railway up
```

### 3. VPS (DigitalOcean Droplet/Linode)

**Fordeler:**
- Full kontroll
- Billigste alternativ ($20-50/måned)
- Kan kjøre alt på én server

### 4. AWS/Google Cloud

**Fordeler:**
- Enterprise-grade
- Meget skalerbart
- Kan være dyrt

## Rask deployment med Railway (Anbefalt for testing)

### Steg 1: Forbered prosjektet

```bash
# Opprett produksjon miljøfil
cp env.example .env.prod

# Rediger .env.prod med produksjonsinnstillinger
nano .env.prod
```

### Steg 2: Deploy til Railway

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialiser prosjekt
railway init

# Deploy
railway up
```

### Steg 3: Konfigurer miljøvariabler

I Railway dashboard:
1. Gå til ditt prosjekt
2. Klikk på hver service (frontend, api-gateway, rag-engine)
3. Legg til miljøvariabler:
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (får du fra Railway PostgreSQL)
   - `REDIS_URL` (får du fra Railway Redis)

### Steg 4: Test deployment

Etter deployment får du en URL som `https://your-app.railway.app`

## Enkelt Docker deployment på VPS

### Steg 1: Sett opp server

```bash
# På en Ubuntu 22.04 server
sudo apt update
sudo apt install docker.io docker-compose-plugin git

# Klon repo
git clone https://github.com/your-username/GPSRAG.git
cd GPSRAG
```

### Steg 2: Konfigurer miljø

```bash
# Kopier miljøfil
cp env.example .env

# Rediger med produksjonsinnstillinger
nano .env
```

### Steg 3: Start applikasjon

```bash
# Bygg og start
docker compose -f docker-compose.prod.yml up -d

# Sjekk status
docker compose -f docker-compose.prod.yml ps
```

### Steg 4: Sett opp domene (valgfritt)

1. Kjøp domene (f.eks. gpsrag.no)
2. Pek A-record til server IP
3. Oppdater nginx.conf med ditt domene
4. Få SSL-sertifikat med Certbot

## Sikkerhet og produksjonsklar

### Viktige endringer for produksjon:

1. **Endre passord og secrets**
2. **Aktiver HTTPS**
3. **Konfigurer backup**
4. **Sett opp monitoring**
5. **Aktiver rate limiting**

### Miljøvariabler for produksjon:

```env
# Sikkerhetsinnstillinger
DEBUG=false
ENVIRONMENT=production

# Sterke passord
POSTGRES_PASSWORD=very-secure-password-here
JWT_SECRET=random-256-bit-secret
SECRET_KEY=another-secure-secret

# API URL (bytt til ditt domene)
NEXT_PUBLIC_API_URL=https://your-domain.com/api
```

## Kjappe instruksjoner for Railway

1. **Registrer deg på Railway.app**
2. **Koble GitHub-kontoen din**
3. **Klikk "Deploy from GitHub repo"**
4. **Velg GPSRAG repository**
5. **Railway oppdager automatisk Docker setup**
6. **Legg til miljøvariabler i dashboard**
7. **Ferdig! Du får en URL**

Vil du at jeg skal hjelpe deg med ett av disse alternativene? 
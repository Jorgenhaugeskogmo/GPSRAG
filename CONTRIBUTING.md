# Bidragsinstruksjoner for GPSRAG

## 🤝 Velkommen som bidragsyter!

Vi setter stor pris på alle bidrag til GPSRAG-prosjektet. Denne guiden vil hjelpe deg å komme i gang med å bidra til prosjektet.

## 🚀 Kom i gang

### Forutsetninger
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Oppsett av utviklingsmiljø

1. **Fork og klon prosjektet**
   ```bash
   git clone https://github.com/din-bruker/GPSRAG.git
   cd GPSRAG
   ```

2. **Kjør oppsettscriptet**
   ```bash
   ./scripts/setup.sh
   ```

3. **Start utviklingsmiljøet**
   ```bash
   # Start kun infrastrukturdatabase-tjenester
   docker-compose up -d postgres weaviate redis minio
   
   # Start backend i development mode
   cd services/api-gateway
   source ../../venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Start frontend i et annet terminal
   cd frontend
   npm run dev
   ```

## 📝 Koding Standarder

### Python Kode
- Følg PEP 8 style guide
- Bruk type hints der det er mulig
- Maks linjelengde: 88 karakterer (Black standard)
- Bruk descriptive variabelnavn

### TypeScript/React Kode
- Bruk TypeScript for alle nye komponenter
- Følg React best practices
- Bruk functional components med hooks
- Props skal være typet med interfaces

### Commit Meldinger
Bruk conventional commit format:
```
type(scope): beskrivelse

[optional body]

[optional footer]
```

Eksempler:
- `feat(chat): legg til WebSocket-støtte for sanntids chat`
- `fix(api): rett HTTP 500 feil i document upload`
- `docs(readme): oppdater installasjonsinstruksjoner`

### Branch Navngiving
- `feature/beskrivelse` - for nye funksjoner
- `fix/beskrivelse` - for bugfikser  
- `docs/beskrivelse` - for dokumentasjonsoppdateringer
- `refactor/beskrivelse` - for refaktorering

## 🧪 Testing

### Kjøre tester
```bash
# Backend tester
cd services/api-gateway
pytest

# Frontend tester
cd frontend
npm test

# Integration tester
./scripts/run-tests.sh
```

### Skrive tester
- Skriv enhetstester for all ny funksjonalitet
- Legg til integrasjonstester for API-endepunkter
- Test edge cases og feilscenarier

## 📋 Pull Request Prosess

1. **Opprett en feature branch**
   ```bash
   git checkout -b feature/din-funksjon
   ```

2. **Gjør endringene dine**
   - Skriv ren, godt dokumentert kode
   - Legg til tester for ny funksjonalitet
   - Oppdater dokumentasjon hvis nødvendig

3. **Test lokalt**
   ```bash
   # Kjør alle tester
   ./scripts/run-tests.sh
   
   # Sjekk kode-kvalitet
   cd services/api-gateway
   black . && isort . && flake8 .
   
   cd ../../frontend
   npm run lint
   ```

4. **Commit og push**
   ```bash
   git add .
   git commit -m "feat(scope): beskrivelse av endringen"
   git push origin feature/din-funksjon
   ```

5. **Opprett Pull Request**
   - Gi en detaljert beskrivelse av endringene
   - Link til relevante issues
   - Legg til skjermbilder hvis relevant

## 🐛 Rapporter Bugs

Når du rapporterer bugs, inkluder:
- Detaljert beskrivelse av problemet
- Steg for å reprodusere
- Forventet vs faktisk oppførsel  
- Screenshots/logger hvis relevant
- Miljøinformasjon (OS, browser, versjon)

## 💡 Foreslå nye funksjoner

For nye funksjoner:
- Sjekk først om det finnes eksisterende issues
- Beskriv use case og motivasjon
- Foreslå implementasjonsapproach
- Diskuter med maintainers før du starter

## 📚 Dokumentasjon

### API Dokumentasjon
- Dokumenter alle nye API-endepunkter
- Bruk docstrings for Python-funksjoner
- Oppdater OpenAPI/Swagger specs

### Komponent Dokumentasjon
- Dokumenter React-komponenter med JSDoc
- Inkluder props-beskrivelser
- Legg til usage examples

## 🔍 Kode Review

Når du gjør kode review:
- Sjekk logikk og algoritmer
- Verifiser at tester dekker funksjonaliteten
- Sjekk sikkerhetsaspekter
- Verifiser at dokumentasjon er oppdatert

## 🏷️ Labels og Prioritering

Vi bruker følgende labels:
- `bug` - Bugfikser
- `enhancement` - Nye funksjoner
- `documentation` - Dokumentasjonsendringer
- `good first issue` - Godt for nye bidragsytere
- `help wanted` - Trenger eksterne bidrag
- `priority: high/medium/low` - Prioritetsnivå

## 🤖 Automatiserte Sjekker

All kode må passere:
- Unit tests
- Integration tests
- Linting (flake8, eslint)
- Type checking (mypy, typescript)
- Security scanning
- Build tests

## 📞 Få Hjelp

Hvis du trenger hjelp:
- Opprett en issue med `question` label
- Se eksisterende dokumentasjon
- Spør i pull request-kommentarer

## 🎉 Anerkjennelse

Alle bidragsytere vil bli anerkjent i:
- README contributors-seksjon
- Release notes for større bidrag
- Hall of fame for betydelige bidrag

Takk for at du bidrar til GPSRAG! 🚀 
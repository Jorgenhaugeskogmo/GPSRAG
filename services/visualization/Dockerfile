FROM python:3.11-slim

WORKDIR /app

# Installer systemavhengigheter
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Kopier requirements og installer Python-avhengigheter
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopier applikasjonskode
COPY . .

# Eksporter port
EXPOSE 8003

# Start applikasjonen
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"] 
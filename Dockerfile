# Basis-Image: Schlankes Python 3.11
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten (falls nötig, hier leer für minimales Setup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den Rest des Codes kopieren
COPY . .

# Verzeichnis für die Datenbank erstellen (für Volume-Mount auf Synology)
RUN mkdir -p /app/data

# Port 8000 freigeben
EXPOSE 8000

# Start-Befehl (ohne --reload für Produktion)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

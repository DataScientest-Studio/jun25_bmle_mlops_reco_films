FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (y compris les outils de build pour scikit-surprise)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY docker/api/requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source (src sera monté en volume, mais on copie pour le build)
COPY src /app/src

# Exposer le port de l'API
EXPOSE 8000

# Commande par défaut
# Note: PYTHONPATH doit être défini pour que les imports fonctionnent
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]


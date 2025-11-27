FROM python:3.11-slim

# ====== 1. Dépendances système ======
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# ====== 2. Installer uv (ultra rapide) ======
RUN pip install uv

# ====== 3. Préparer le répertoire ======
WORKDIR /app

# ====== 4. Installer les dépendances Python (utilisation du cache Docker) ======

# Copier seulement requirements pour profiter du cache
COPY docker/api/requirements.txt /app/requirements.txt

# Installation des deps AVANT de copier le code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r /app/requirements.txt

# ====== 5. Copier ensuite le code source ======
# (ne casse plus la couche d'installation des requirements)
COPY src /app/src

# ====== 6. Scripts cron, init et API ======
COPY docker/api/start_api.sh      /app/start_api.sh

RUN chmod +x \
    /app/start_api.sh

# ====== 7. Variables d’environnement ======
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["/app/start_api.sh"]

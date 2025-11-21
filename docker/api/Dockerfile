FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (y compris les outils de build pour scikit-surprise)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY docker/api/requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source (src sera monté en volume, mais on copie pour le build)
COPY src /app/src

# Copier les scripts cron
COPY docker/api/cron_training.sh /app/docker/api/cron_training.sh
COPY docker/api/init_cron.sh /app/docker/api/init_cron.sh
RUN chmod +x /app/docker/api/cron_training.sh /app/docker/api/init_cron.sh

# Exposer le port de l'API
EXPOSE 8000

# Commande par défaut
# Note: PYTHONPATH doit être défini pour que les imports fonctionnent
ENV PYTHONPATH=/app/src

# Script de démarrage qui lance cron et l'API
COPY docker/api/start_api.sh /app/start_api.sh
RUN chmod +x /app/start_api.sh
CMD ["/app/start_api.sh"]


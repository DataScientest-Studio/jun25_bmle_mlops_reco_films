FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Installer uv (installateur ultra-rapide)
RUN pip install --no-cache-dir uv

# Copier et installer les dépendances Python
COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r /app/requirements.txt

# Copier le code de l'application
COPY . /app

# Télécharger et installer mc (MinIO client)
RUN wget -q https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/bin/mc \
    && chmod +x /usr/bin/mc

# Copier et rendre exécutable le script d'init MLflow
COPY init_mlflow.sh /app/init_mlflow.sh
RUN chmod +x /app/init_mlflow.sh

# Créer le dossier pour le backend SQLite (lié à un volume Docker)
RUN mkdir -p /mlflow

# Commande par défaut : exécuter le script d'init MLflow
CMD ["/app/init_mlflow.sh"]

# Utilise une image Python légère
FROM python:3.9-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie les fichiers de dépendances
COPY ./docker/api/requirements.txt /app/requirements.txt

# Installe les dépendances
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port de l'API
EXPOSE 8000

# Commande pour lancer l'API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

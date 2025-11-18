FROM python:3.9-slim

WORKDIR /app

# Copier le script d'initialisation
COPY wait-for-db.sh /app/wait-for-db.sh
COPY init_import_data.sh /app/init_import_data.sh
RUN chmod +x /app/wait-for-db.sh /app/init_import_data.sh

RUN apt-get update && apt-get install -y netcat-openbsd

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

# Démarrage via le script
CMD ["/app/init_import_data.sh"]

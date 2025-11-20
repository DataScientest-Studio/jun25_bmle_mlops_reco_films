FROM minio/minio:latest

WORKDIR /app

# Copier le script d'initialisation
COPY init_minio.sh /app/init_minio.sh
RUN chmod +x /app/init_minio.sh

# Exposer les ports MinIO
EXPOSE 9000 9001

# Démarrage via le script
ENTRYPOINT ["/app/init_minio.sh"]

#!/bin/sh
set -e

echo "Demarrage de MinIO avec initialisation automatique..."

# Lancer MinIO en arriere-plan
minio server /data --console-address ":9001" &
MINIO_PID=$!

# Attendre que MinIO soit pret
echo "Attente du service MinIO..."
until curl -s http://localhost:9000/minio/health/ready >/dev/null; do
  echo "MinIO pas encore pret, attente 2s..."
  sleep 2
done
echo "MinIO est pret"

# Configurer mc (client MinIO)
echo " Configuration du client mc..."
mc alias set local http://localhost:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --api S3v4

# Creer les buckets necessaires
for bucket in mlflow-artifacts dvc-storage; do
  if ! mc ls local/$bucket >/dev/null 2>&1; then
    echo "Creation du bucket $bucket..."
    mc mb local/$bucket
  else
    echo "Bucket $bucket existe deja "
  fi
done

echo "Buckets prets : mlflow-artifacts, dvc-storage"
echo "MinIO operationnel"

# Garder MinIO actif
wait $MINIO_PID

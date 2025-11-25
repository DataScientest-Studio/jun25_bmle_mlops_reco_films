#!/bin/sh
set -e

echo "ðŸš€ DÃ©marrage de MinIO avec initialisation automatique..."

# Lancer MinIO en arriÃ¨re-plan
minio server /data --console-address ":9001" &
MINIO_PID=$!

# Attendre que MinIO soit prÃªt
echo "â³ Attente du service MinIO..."
until curl -s http://localhost:9000/minio/health/ready >/dev/null; do
  echo "MinIO pas encore prÃªt, attente 2s..."
  sleep 2
done
echo "âœ… MinIO est prÃªt"

# Configurer mc (client MinIO)
echo "ðŸ”§ Configuration du client mc..."
mc alias set local http://localhost:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --api S3v4

# CrÃ©er les buckets nÃ©cessaires
for bucket in mlflow-artifacts dvc-storage; do
  if ! mc ls local/$bucket >/dev/null 2>&1; then
    echo "ðŸª£ CrÃ©ation du bucket $bucket..."
    mc mb local/$bucket
  else
    echo "âœ… Bucket $bucket existe dÃ©jÃ "
  fi
done

echo "âœ… Buckets prÃªts : mlflow-artifacts, dvc-storage"
echo "ðŸš€ MinIO opÃ©rationnel"

# Garder MinIO actif
wait $MINIO_PID

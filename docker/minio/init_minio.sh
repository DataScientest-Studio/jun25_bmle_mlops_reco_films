#!/bin/sh
set -e

echo "🚀 Démarrage de MinIO avec initialisation automatique..."

# Lancer MinIO en arrière-plan
minio server /data --console-address ":9001" &
MINIO_PID=$!

# Attendre que MinIO soit prêt
echo "⏳ Attente du service MinIO..."
until curl -s http://localhost:9000/minio/health/ready >/dev/null; do
  echo "MinIO pas encore prêt, attente 2s..."
  sleep 2
done
echo "✅ MinIO est prêt"

# Configurer mc (client MinIO)
echo "🔧 Configuration du client mc..."
mc alias set local http://localhost:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --api S3v4

# Créer les buckets nécessaires
for bucket in mlflow-artifacts dvc-storage; do
  if ! mc ls local/$bucket >/dev/null 2>&1; then
    echo "🪣 Création du bucket $bucket..."
    mc mb local/$bucket
  else
    echo "✅ Bucket $bucket existe déjà"
  fi
done

echo "✅ Buckets prêts : mlflow-artifacts, dvc-storage"
echo "🚀 MinIO opérationnel"

# Garder MinIO actif
wait $MINIO_PID

#!/bin/sh
set -e

echo "ðŸš€ Initialisation MLflow avec MinIO..."

# CrÃ©er le dossier du backend store si nÃ©cessaire
mkdir -p /mlflow
echo "âœ… Dossier /mlflow prÃªt pour le backend store"

# Attendre que MinIO soit prÃªt via mc
echo "â³ Attente de MinIO..."
until mc alias set local "${MLFLOW_S3_ENDPOINT_URL:-http://minio:9000}" "${AWS_ACCESS_KEY_ID}" "${AWS_SECRET_ACCESS_KEY}" --api S3v4 >/dev/null 2>&1; do
  echo "MinIO pas encore prÃªt, attente 2s..."
  sleep 2
done
echo "âœ… MinIO prÃªt"

# CrÃ©er bucket si nÃ©cessaire
if ! mc ls local/mlflow-artifacts >/dev/null 2>&1; then
  echo "ðŸª£ CrÃ©ation du bucket mlflow-artifacts..."
  mc mb local/mlflow-artifacts
else
  echo "âœ… Bucket mlflow-artifacts existe dÃ©jÃ "
fi

echo "âœ… Initialisation MLflow terminÃ©e."
echo "ðŸš€ DÃ©marrage du serveur MLflow..."

# Lancer MLflow server en avant-plan
exec mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri sqlite:////mlflow/mlflow.db \
    --default-artifact-root s3://mlflow-artifacts

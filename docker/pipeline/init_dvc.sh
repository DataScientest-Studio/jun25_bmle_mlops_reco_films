#!/bin/sh
set -e

echo "ðŸš€ Initialisation DVC et pipeline..."

# Initialiser DVC si pas encore fait
if [ ! -d ".dvc" ]; then
    echo "ðŸ”¹ DVC non initialisÃ©, crÃ©ation du dÃ©pÃ´t DVC..."
    dvc init
fi

# Attendre que MinIO soit prÃªt
echo "â³ Attente de MinIO..."
until curl -s ${DVC_S3_ENDPOINT:-http://minio:9000}/minio/health/ready >/dev/null; do
  echo "MinIO pas encore prÃªt, attente 2s..."
  sleep 2
done
echo "âœ… MinIO prÃªt"

# Configurer le remote DVC S3 si non existant
if ! dvc remote list | grep -q "^myremote"; then
    echo "ðŸ”¹ Ajout du remote DVC myremote..."
    dvc remote add -d myremote "${DVC_REMOTE_URL}"
else
    echo "âš¡ Remote 'myremote' dÃ©jÃ  configurÃ©, utilisation existante."
fi

# Modifier la configuration du remote
dvc remote modify myremote endpointurl "${DVC_S3_ENDPOINT}"
dvc remote modify myremote access_key_id "${AWS_ACCESS_KEY_ID}"
dvc remote modify myremote secret_access_key "${AWS_SECRET_ACCESS_KEY}"

echo "âœ… Remote DVC configurÃ© : ${DVC_REMOTE_URL} (${DVC_S3_ENDPOINT})"

# (Optionnel) VÃ©rifier la connexion Ã  MLflow
if [ -n "$MLFLOW_TRACKING_URI" ]; then
  echo "ðŸ”— MLflow tracking URI : $MLFLOW_TRACKING_URI"
  echo "âœ… MLflow prÃªt Ã  recevoir les logs dâ€™expÃ©riences"
fi

# Ajouter src au PYTHONPATH pour les imports
export PYTHONPATH=$(pwd)

# Garder le conteneur en vie pour exécution manuelle
echo "DVC configuré. Conteneur prêt pour exécution manuelle."
tail -f /dev/null
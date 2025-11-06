#!/bin/sh
set -e

echo "🚀 Initialisation DVC et pipeline..."

# Initialiser DVC si pas encore fait
if [ ! -d ".dvc" ]; then
    echo "🔹 DVC non initialisé, création du dépôt DVC..."
    dvc init
fi

# Attendre que MinIO soit prêt
echo "⏳ Attente de MinIO..."
until curl -s ${DVC_S3_ENDPOINT:-http://minio:9000}/minio/health/ready >/dev/null; do
  echo "MinIO pas encore prêt, attente 2s..."
  sleep 2
done
echo "✅ MinIO prêt"

# Configurer le remote DVC S3 si non existant
if ! dvc remote list | grep -q "^myremote"; then
    echo "🔹 Ajout du remote DVC myremote..."
    dvc remote add -d myremote "${DVC_REMOTE_URL}"
else
    echo "⚡ Remote 'myremote' déjà configuré, utilisation existante."
fi

# Modifier la configuration du remote
dvc remote modify myremote endpointurl "${DVC_S3_ENDPOINT}"
dvc remote modify myremote access_key_id "${AWS_ACCESS_KEY_ID}"
dvc remote modify myremote secret_access_key "${AWS_SECRET_ACCESS_KEY}"

echo "✅ Remote DVC configuré : ${DVC_REMOTE_URL} (${DVC_S3_ENDPOINT})"

# (Optionnel) Vérifier la connexion à MLflow
if [ -n "$MLFLOW_TRACKING_URI" ]; then
  echo "🔗 MLflow tracking URI : $MLFLOW_TRACKING_URI"
  echo "✅ MLflow prêt à recevoir les logs d’expériences"
fi

# Ajouter src au PYTHONPATH pour les imports
export PYTHONPATH=$(pwd)/src

echo "🚀 Exécution des stages DVC..."

# Exécuter tous les stages dans le bon ordre
# DVC ne va créer que les fichiers manquants ou les stages dont les entrées ont changé
dvc repro

echo "🎬 Pipeline DVC terminé avec succès."

# ✅ Pousser les fichiers suivis par DVC vers MinIO
echo "⬆️ Pousser les fichiers DVC vers MinIO..."
dvc push
echo "✅ Fichiers DVC envoyés vers MinIO."
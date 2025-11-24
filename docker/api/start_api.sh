#!/bin/bash
# Script de dÃ©marrage qui lance cron et l'API

# Initialiser cron
/app/docker/api/init_cron.sh

# ====== Configuration DVC ======
echo "🔧 Configuration DVC..."

# Initialiser DVC si pas encore fait
if [ ! -d ".dvc" ]; then
    echo "🔸 DVC non initialisé, création du dépôt DVC..."
    dvc init --no-scm
fi

# Configurer le remote DVC S3 si non existant
if ! dvc remote list | grep -q "^myremote"; then
    echo "🔸 Ajout du remote DVC myremote..."
    dvc remote add -d myremote "${DVC_REMOTE_URL}"
else
    echo "⚡ Remote 'myremote' déjà configuré."
fi

# Modifier la configuration du remote (toujours appliquer pour être sûr)
dvc remote modify myremote endpointurl "${DVC_S3_ENDPOINT}"
dvc remote modify myremote access_key_id "${AWS_ACCESS_KEY_ID}"
dvc remote modify myremote secret_access_key "${AWS_SECRET_ACCESS_KEY}"

echo "✅ DVC configuré."

# Lancer l'API
exec uvicorn api.app:app --host 0.0.0.0 --port 8000


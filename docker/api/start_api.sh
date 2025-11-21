#!/bin/bash
# Script de démarrage qui lance cron et l'API

# Initialiser cron
/app/docker/api/init_cron.sh

# Lancer l'API
exec uvicorn api.app:app --host 0.0.0.0 --port 8000


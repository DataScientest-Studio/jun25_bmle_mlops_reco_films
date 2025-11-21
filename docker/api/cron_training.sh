#!/bin/bash
# Script cron pour l'entraînement planifié
# Exécute l'entraînement tous les jours à 2h du matin

# Configuration
API_URL="${API_URL:-http://localhost:8000}"

# Logs
LOG_FILE="/app/logs/cron_training.log"
mkdir -p /app/logs

# Exécuter l'entraînement via l'API
echo "$(date): Démarrage de l'entraînement planifié" >> "$LOG_FILE"
curl -X POST "${API_URL}/training/" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' \
  >> "$LOG_FILE" 2>&1
echo "$(date): Fin de l'entraînement planifié" >> "$LOG_FILE"


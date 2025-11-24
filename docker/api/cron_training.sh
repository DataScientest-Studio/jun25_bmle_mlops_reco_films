#!/bin/bash
# Script cron pour l'entraÃ®nement planifiÃ©
# ExÃ©cute l'entraÃ®nement tous les jours Ã  2h du matin

# Configuration
API_URL="${API_URL:-http://localhost:8000}"

# Logs
LOG_FILE="/app/logs/cron_training.log"
mkdir -p /app/logs

# ExÃ©cuter l'entraÃ®nement via l'API
echo "$(date): DÃ©marrage de l'entraÃ®nement planifiÃ©" >> "$LOG_FILE"
curl -X POST "${API_URL}/training/" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' \
  >> "$LOG_FILE" 2>&1
echo "$(date): Fin de l'entraÃ®nement planifiÃ©" >> "$LOG_FILE"


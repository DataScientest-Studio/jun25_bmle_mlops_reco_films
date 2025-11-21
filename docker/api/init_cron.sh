#!/bin/bash
# Script d'initialisation de cron pour l'entraînement planifié

# Créer le répertoire pour les logs
mkdir -p /app/logs

# Copier le script cron
cp /app/docker/api/cron_training.sh /app/cron_training.sh
chmod +x /app/cron_training.sh

# Configurer le crontab (tous les jours à 2h du matin)
echo "0 2 * * * /app/cron_training.sh >> /app/logs/cron_training.log 2>&1" | crontab -

# Démarrer cron en arrière-plan
cron

echo "Cron configuré pour l'entraînement planifié (tous les jours à 2h)"


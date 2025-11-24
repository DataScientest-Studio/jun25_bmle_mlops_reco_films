#!/bin/sh

echo "DÃ©marrage de init_db..."
export PGPASSWORD='reco_films'

echo "Test de connexion Ã  PostgreSQL..."
until psql -h db -U reco_films -d reco_films -c "SELECT 1" > /dev/null 2>&1; do
  echo "En attente de la base de donnÃ©es..."
  sleep 2
done

echo "Connexion Ã  PostgreSQL rÃ©ussie !"
echo "ExÃ©cution du script SQL..."
psql -h db -U reco_films -d reco_films -f /scripts/create_table.sql

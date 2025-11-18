#!/bin/sh
# Attendre que le port 5432 de $1 soit disponible
set -e
host="$1"
# Pas de shift ici, car on n'a pas besoin des arguments suivants
# On attend juste que la base soit prête

until nc -z "$host" 5432; do
  echo "Waiting for PostgreSQL at $host..."
  sleep 1
done

echo "PostgreSQL is up!"
# Ne pas utiliser exec ici, car on n'a pas de commande à exécuter après
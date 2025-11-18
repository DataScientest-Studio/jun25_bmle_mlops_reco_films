#!/bin/sh

# Attendre que la base de données soit prête
/app/wait-for-db.sh db 5432

# Exécute check_db.py et stocke le résultat
python /scripts/check_db.py
DB_STATUS=$?

if [ "$DB_STATUS" -eq "1" ]; then
    python /scripts/import_data.py
else
    echo "La base de données est déjà remplie. Passage à l'étape suivante."
fi

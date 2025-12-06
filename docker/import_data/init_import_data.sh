#!/bin/sh

# Attendre que la base de donnees soit prete
/app/wait-for-db.sh db 5432

# Execute check_db.py et stocke le resultat
python /scripts/check_db.py
DB_STATUS=$?

if [ "$DB_STATUS" -eq "1" ]; then
    python /scripts/import_data.py
else
    echo "La base de donnees est deja remplie. Passage a l'etape suivante."
fi

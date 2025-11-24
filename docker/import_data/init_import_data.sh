#!/bin/sh

# Attendre que la base de donnÃ©es soit prÃªte
/app/wait-for-db.sh db 5432

# ExÃ©cute check_db.py et stocke le rÃ©sultat
python /scripts/check_db.py
DB_STATUS=$?

if [ "$DB_STATUS" -eq "1" ]; then
    python /scripts/import_data.py
else
    echo "La base de donnÃ©es est dÃ©jÃ  remplie. Passage Ã  l'Ã©tape suivante."
fi

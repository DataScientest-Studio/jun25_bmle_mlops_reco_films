#!/bin/bash
set -e

# La base de données reco_films est déjà créée via POSTGRES_DB
# On s'assure juste que l'utilisateur a les droits
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_USER";
EOSQL

# Création de l'utilisateur et de la base de données pour Airflow
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'airflow') THEN
    CREATE USER airflow WITH PASSWORD 'airflow';
        END IF;
    END
    \$\$;
    
    SELECT 'CREATE DATABASE airflow'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
    
    GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

# Exécution du script SQL de création de tables pour l'application
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /scripts/create_table.sql

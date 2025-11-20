import psycopg2
from sqlalchemy import create_engine, text

# Configuration de la connexion à PostgreSQL
db_config = {
    "host": "db",
    "database": "reco_films",
    "user": "reco_films",
    "password": "reco_films",
}

def is_db_populated():
    try:
        engine = create_engine(f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")
        with engine.connect() as conn:
            # Utilise text() pour encapsuler la requête SQL
            result = conn.execute(text("SELECT COUNT(*) FROM movies;"))
            count = result.scalar()
            return count == 0  # Retourne True si la table est vide
    except Exception as e:
        print(f"Erreur lors de la vérification de la base de données : {e}")
        return True  # En cas d'erreur, on suppose que la base de données doit être remplie

if __name__ == "__main__":
    if is_db_populated():
        print("1")  # Code de sortie 1 pour indiquer que la base de données doit être remplie
        exit(1)
    else:
        print("0")  # Code de sortie 0 pour indiquer que la base de données est déjà remplie
        exit(0)

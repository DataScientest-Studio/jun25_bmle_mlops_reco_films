import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine

def get_db_engine():
    """Établit une connexion à la base de données PostgreSQL via SQLAlchemy."""
    db_user = os.getenv("DB_USER", "reco_films")
    db_password = os.getenv("DB_PASSWORD", "reco_films")
    db_host = os.getenv("DB_HOST", "db")
    db_name = os.getenv("DB_NAME", "reco_films")
    
    return create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")

def load_filtered_ratings(min_ratings_user=50, min_ratings_movie=100):
    """
    Charge les notes depuis la base de données en appliquant des filtres 
    sur l'activité des utilisateurs et la popularité des films.
    """
    engine = get_db_engine()
    
    query = """
        WITH
        active_users AS (
            SELECT user_id
            FROM ratings
            GROUP BY user_id
            HAVING COUNT(*) >= %(min_ratings_user)s
        ),
        popular_movies AS (
            SELECT movie_id
            FROM ratings
            GROUP BY movie_id
            HAVING COUNT(*) >= %(min_ratings_movie)s
        )
        SELECT r.user_id, r.movie_id, r.rating
        FROM ratings r
        JOIN active_users au ON r.user_id = au.user_id
        JOIN popular_movies pm ON r.movie_id = pm.movie_id
    """
    
    try:
        print(f"Chargement des données avec filtres : min_ratings_user={min_ratings_user}, min_ratings_movie={min_ratings_movie}")
        # Use a connection from the engine for read_sql
        with engine.connect() as conn:
            ratings_df = pd.read_sql(query, conn, params={"min_ratings_user": min_ratings_user, "min_ratings_movie": min_ratings_movie})
        print(f"Données chargées : {len(ratings_df)} lignes.")
        return ratings_df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        raise e


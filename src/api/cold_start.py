"""
Module pour gérer le problème du Cold Start
- Nouveaux utilisateurs : recommandations basées sur films populaires/genres
- Nouveaux films : recommandations basées sur similarité de genres
"""
import logging
import pandas as pd
import psycopg2
from typing import List, Tuple, Optional
from pipeline.config import load_config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Établit une connexion à PostgreSQL"""
    config = load_config()
    return psycopg2.connect(
        dbname=config["db"]["dbname"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )


def is_new_user(user_id: int) -> bool:
    """Vérifie si un utilisateur est nouveau (pas de ratings)"""
    conn = get_db_connection()
    try:
        query = "SELECT COUNT(*) FROM ratings WHERE user_id = %s"
        count = pd.read_sql(query, conn, params=(user_id,)).iloc[0, 0]
        return count == 0
    finally:
        conn.close()


def is_new_movie(movie_id: int) -> bool:
    """Vérifie si un film est nouveau (pas de ratings)"""
    conn = get_db_connection()
    try:
        query = "SELECT COUNT(*) FROM ratings WHERE movie_id = %s"
        count = pd.read_sql(query, conn, params=(movie_id,)).iloc[0, 0]
        return count == 0
    finally:
        conn.close()


def get_popular_movies(N: int = 10) -> List[Tuple[str, float]]:
    """
    Retourne les N films les plus populaires (basés sur nombre de ratings et moyenne)
    Format: [(title, score), ...]
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            m.title,
            COUNT(r.rating) as num_ratings,
            AVG(r.rating) as avg_rating,
            (COUNT(r.rating) * AVG(r.rating)) / (COUNT(r.rating) + 100) as popularity_score
        FROM movies m
        LEFT JOIN ratings r ON m.movie_id = r.movie_id
        GROUP BY m.movie_id, m.title
        HAVING COUNT(r.rating) >= 10
        ORDER BY popularity_score DESC, num_ratings DESC
        LIMIT %s
        """
        df = pd.read_sql(query, conn, params=(N,))
        return [(row['title'], float(row['popularity_score'])) for _, row in df.iterrows()]
    finally:
        conn.close()


def get_popular_movies_by_genre(genre: Optional[str] = None, N: int = 10) -> List[Tuple[str, float]]:
    """
    Retourne les N films les plus populaires d'un genre spécifique
    Si genre est None, retourne les films populaires tous genres confondus
    """
    conn = get_db_connection()
    try:
        if genre:
            query = """
            SELECT 
                m.title,
                COUNT(r.rating) as num_ratings,
                AVG(r.rating) as avg_rating,
                (COUNT(r.rating) * AVG(r.rating)) / (COUNT(r.rating) + 100) as popularity_score
            FROM movies m
            JOIN movie_genres mg ON m.movie_id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.genre_id
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE g.name = %s
            GROUP BY m.movie_id, m.title
            HAVING COUNT(r.rating) >= 10
            ORDER BY popularity_score DESC, num_ratings DESC
            LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(genre, N))
        else:
            query = """
            SELECT 
                m.title,
                COUNT(r.rating) as num_ratings,
                AVG(r.rating) as avg_rating,
                (COUNT(r.rating) * AVG(r.rating)) / (COUNT(r.rating) + 100) as popularity_score
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id, m.title
            HAVING COUNT(r.rating) >= 10
            ORDER BY popularity_score DESC, num_ratings DESC
            LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(N,))
        
        return [(row['title'], float(row['popularity_score'])) for _, row in df.iterrows()]
    finally:
        conn.close()


def get_user_preferred_genres(user_id: int, top_k: int = 3) -> List[str]:
    """
    Retourne les genres préférés d'un utilisateur basés sur ses ratings
    (même si l'utilisateur est nouveau, on peut utiliser ses quelques ratings)
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            g.name,
            AVG(r.rating) as avg_rating,
            COUNT(r.rating) as num_ratings
        FROM ratings r
        JOIN movie_genres mg ON r.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        WHERE r.user_id = %s
        GROUP BY g.name
        HAVING COUNT(r.rating) >= 1
        ORDER BY avg_rating DESC, num_ratings DESC
        LIMIT %s
        """
        df = pd.read_sql(query, conn, params=(user_id, top_k))
        return df['name'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_cold_start_recommendations(user_id: int, N: int = 5) -> List[Tuple[str, float]]:
    """
    Génère des recommandations pour un nouvel utilisateur (cold start)
    Stratégie:
    1. Si l'utilisateur a quelques ratings, utiliser ses genres préférés
    2. Sinon, utiliser les films les plus populaires
    """
    # Vérifier si l'utilisateur a quelques ratings
    conn = get_db_connection()
    try:
        query = "SELECT COUNT(*) FROM ratings WHERE user_id = %s"
        rating_count = pd.read_sql(query, conn, params=(user_id,)).iloc[0, 0]
    finally:
        conn.close()
    
    if rating_count > 0:
        # Utilisateur avec quelques ratings : utiliser genres préférés
        preferred_genres = get_user_preferred_genres(user_id, top_k=3)
        if preferred_genres:
            # Prendre des films des genres préférés
            recommendations = []
            films_per_genre = max(2, N // len(preferred_genres) + 1)
            for genre in preferred_genres[:3]:
                genre_movies = get_popular_movies_by_genre(genre, N=films_per_genre)
                recommendations.extend(genre_movies)
            # Trier par score et prendre les top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:N]
    
    # Utilisateur complètement nouveau : films populaires
    return get_popular_movies(N=N)


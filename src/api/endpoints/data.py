"""
Endpoints pour générer des données aléatoires et récupérer des votes
"""
import logging
import random
import os
import pandas as pd
import psycopg2
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from api.schemas import HealthResponse
from pipeline.config import load_config
from typing import Optional

logger = logging.getLogger(__name__)
# Router sans prefix pour correspondre aux endpoints du collègue
router = APIRouter(tags=["data"])


def get_db_connection():
    """Crée une connexion à la base de données"""
    config = load_config()
    return psycopg2.connect(
        dbname=config["db"]["dbname"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )


@router.post("/generate-ratings")
async def generate_random_ratings(
    batch_size: int = 10000
):
    """
    Génère des votes (ratings) aléatoires dans la base de données.
    
    Compatible avec l'API du collègue : POST /generate-ratings/?batch_size=30000
    
    - **batch_size**: Nombre de votes à générer (défaut: 10000)
    """
    return await generate_random_ratings_internal(count=batch_size)


@router.post("/generate/ratings")
async def generate_random_ratings_alt(
    count: int = 10000
):
    """
    Génère des votes (ratings) aléatoires dans la base de données.
    
    - **count**: Nombre de votes à générer (défaut: 10000)
    """
    return await generate_random_ratings_internal(count=count)


async def generate_random_ratings_internal(
    count: int = 10000
):
    """
    Génère des votes (ratings) aléatoires dans la base de données.
    
    - **count**: Nombre de votes à générer (défaut: 10000)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO ratings (user_id, movie_id, rating, timestamp)
        SELECT
            u.user_id,
            m.movie_id,
            (FLOOR(RANDOM() * 10) + 1) * 0.5,
            EXTRACT(EPOCH FROM NOW()) * 1000
        FROM
            (SELECT user_id FROM users ORDER BY RANDOM() LIMIT 500) u
        CROSS JOIN
            (SELECT movie_id FROM movies ORDER BY RANDOM() LIMIT 500) m
        LEFT JOIN
            ratings r ON u.user_id = r.user_id AND m.movie_id = r.movie_id
        WHERE
            r.user_id IS NULL
            AND u.user_id IS NOT NULL
            AND m.movie_id IS NOT NULL
        LIMIT %s;
        """

        cursor.execute(query, (count,))
        conn.commit()

        message = f"Inserted {count} new ratings."
        logger.info(message)

        return JSONResponse(content={
            "status": "success", 
            "inserted": count,
            "message": message 
        })  

        for table in ["ratings", "users", "movies"]:
            cursor.execute(f"ANALYZE {table};")
            conn.commit()
            logger.info(f"Analyzed table: {table}")

        return JSONResponse(content={"status": "success", "tables_analyzed": ["ratings", "users", "movies"]})

    except Exception as e:
        logger.error(f"Error generating ratings: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()

    

@router.get("/get-random-ratings")
async def get_random_ratings(
    n: int = 10
):
    """
    Récupère des votes aléatoires de la base de données.
    
    Compatible avec l'API du collègue : GET /get-random-ratings/?n=100000
    
    - **n**: Nombre de votes à récupérer (défaut: 10)
    """
    return await get_random_ratings_internal(count=n)


@router.get("/ratings/random")
async def get_random_ratings_alt(
    count: int = 10,
    user_id: Optional[int] = None
):
    """
    Récupère des votes aléatoires de la base de données.
    
    - **count**: Nombre de votes à récupérer (défaut: 10)
    - **user_id**: Filtrer par ID utilisateur (optionnel)
    """
    return await get_random_ratings_internal(count=count, user_id=user_id)


async def get_random_ratings_internal(
    count: int = 10,
    user_id: Optional[int] = None
):
    """
    Récupère des votes aléatoires de la base de données.
    
    - **count**: Nombre de votes à récupérer (défaut: 10)
    - **user_id**: Filtrer par ID utilisateur (optionnel)
    """
    try:
        conn = get_db_connection()
        
        if user_id:
            query = """
                SELECT r.user_id, r.movie_id, r.rating, r.timestamp, m.title
                FROM ratings r
                JOIN movies m ON r.movie_id = m.movie_id
                WHERE r.user_id = %s
                ORDER BY RANDOM()
                LIMIT %s
            """
            ratings_df = pd.read_sql(query, conn, params=(user_id, count))
        else:
            query = """
                SELECT r.user_id, r.movie_id, r.rating, r.timestamp, m.title
                FROM ratings r
                JOIN movies m ON r.movie_id = m.movie_id
                ORDER BY RANDOM()
                LIMIT %s
            """
            ratings_df = pd.read_sql(query, conn, params=(count,))
        
        conn.close()
        
        if ratings_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Aucun vote trouvé"
            )
        
        return {
            "status": "success",
            "count": len(ratings_df),
            "ratings": ratings_df.to_dict(orient="records")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de votes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de votes: {str(e)}"
        )


@router.get("/stats")
async def get_data_stats():
    """Récupère des statistiques sur les données dans la base"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Compter les utilisateurs
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Compter les films
        cursor.execute("SELECT COUNT(*) FROM movies")
        movie_count = cursor.fetchone()[0]
        
        # Compter les votes
        cursor.execute("SELECT COUNT(*) FROM ratings")
        rating_count = cursor.fetchone()[0]
        
        # Moyenne des votes
        cursor.execute("SELECT AVG(rating) FROM ratings")
        avg_rating = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "stats": {
                "users": user_count,
                "movies": movie_count,
                "ratings": rating_count,
                "average_rating": round(float(avg_rating), 2) if avg_rating else None
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des stats: {str(e)}"
        )


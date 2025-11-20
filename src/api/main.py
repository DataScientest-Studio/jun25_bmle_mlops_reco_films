from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from database import get_db_connection, release_db_connection
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/generate-ratings/")
async def generate_ratings(batch_size: int = Query(10000, description="Nombre d'entrées à générer")):
    """
    Insère un lot de `batch_size` entrées dans la table `ratings`.
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
            users u
        CROSS JOIN
            movies m
        LEFT JOIN
            ratings r ON u.user_id = r.user_id AND m.movie_id = r.movie_id
        WHERE
            r.user_id IS NULL
            AND u.user_id IS NOT NULL
            AND m.movie_id IS NOT NULL
        LIMIT %s;
        """

        cursor.execute(query, (batch_size,))
        conn.commit()
        logger.info(f"Inserted {batch_size} new ratings.")
        return JSONResponse(content={"status": "success", "inserted": batch_size})

    except Exception as e:
        logger.error(f"Error generating ratings: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            release_db_connection(conn)

@app.post("/analyze-tables/")
async def analyze_tables():
    """
    Lance ANALYZE sur les tables `ratings`, `users` et `movies`.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for table in ["ratings", "users", "movies"]:
            cursor.execute(f"ANALYZE {table};")
            conn.commit()
            logger.info(f"Analyzed table: {table}")

        return JSONResponse(content={"status": "success", "tables_analyzed": ["ratings", "users", "movies"]})

    except Exception as e:
        logger.error(f"Error analyzing tables: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            release_db_connection(conn)

@app.get("/get-random-ratings/")
async def get_random_ratings(n: int = Query(500000, description="Nombre de lignes aléatoires à récupérer")):
    """
    Récupère `n` lignes aléatoires de la table `ratings` (user_id, movie_id, rating).
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT user_id, movie_id, rating
        FROM ratings
        ORDER BY RANDOM()
        LIMIT %s;
        """

        cursor.execute(query, (n,))
        results = cursor.fetchall()

        # Convertir les résultats en une liste de dictionnaires avec des floats
        ratings = [
            {"user_id": row[0], "movie_id": row[1], "rating": float(row[2])}
            for row in results
        ]

        logger.info(f"Fetched {len(ratings)} random ratings.")
        return JSONResponse(content={"status": "success", "data": ratings})

    except Exception as e:
        logger.error(f"Error fetching random ratings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            release_db_connection(conn)

@app.get("/")
async def root():
    return {"message": "API pour générer des ratings, analyser les tables et récupérer des données aléatoires."}

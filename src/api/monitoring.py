"""
Module pour monitorer la qualité des recommandations
Métriques: diversité, nouveauté, coverage, etc.
"""
import logging
import pandas as pd
import psycopg2
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import os
from pipeline.config import load_config

logger = logging.getLogger(__name__)

RECOMMENDATIONS_LOG_PATH = os.path.join(os.getenv("METRICS_DIR", "metrics"), "recommendations_log.jsonl")

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


def log_recommendation(
    user_id: int,
    recommendations: List[Tuple[str, float]],
    method: str = "collaborative_filtering"
):
    """
    Enregistre une recommandation dans le log pour monitoring
    Format JSONL (une ligne par recommandation)
    """
    os.makedirs(os.path.dirname(RECOMMENDATIONS_LOG_PATH), exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "method": method,
        "num_recommendations": len(recommendations),
        "recommendations": [
            {"movie": movie, "score": score}
            for movie, score in recommendations
        ]
    }
    
    with open(RECOMMENDATIONS_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def compute_diversity(recommendations: List[Tuple[str, float]]) -> float:
    """
    Calcule la diversité des recommandations
    Basé sur le nombre de films uniques recommandés
    Plus simple: ratio films uniques / total
    """
    unique_movies = len(set([movie for movie, _ in recommendations]))
    total = len(recommendations)
    return unique_movies / total if total > 0 else 0.0


def compute_novelty(
    recommendations: List[Tuple[str, float]],
    popular_movies: Optional[List[str]] = None
) -> float:
    """
    Calcule la nouveauté des recommandations
    Basé sur le ratio de films non-populaires recommandés
    Si popular_movies n'est pas fourni, charge depuis la DB
    """
    if popular_movies is None:
        # Charger les films populaires depuis la DB
        conn = get_db_connection()
        try:
            query = """
            SELECT m.title
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id, m.title
            HAVING COUNT(r.rating) >= 100
            ORDER BY COUNT(r.rating) DESC
            LIMIT 100
            """
            df = pd.read_sql(query, conn)
            popular_movies = df['title'].tolist()
        finally:
            conn.close()
    
    recommended_movies = [movie for movie, _ in recommendations]
    novel_count = sum(1 for movie in recommended_movies if movie not in popular_movies)
    return novel_count / len(recommendations) if recommendations else 0.0


def compute_coverage(
    all_recommendations: List[List[Tuple[str, float]]],
    total_movies: Optional[int] = None
) -> float:
    """
    Calcule le coverage: pourcentage de films du catalogue qui ont été recommandés
    Si total_movies n'est pas fourni, charge depuis la DB
    """
    if total_movies is None:
        conn = get_db_connection()
        try:
            query = "SELECT COUNT(*) FROM movies"
            total_movies = pd.read_sql(query, conn).iloc[0, 0]
        finally:
            conn.close()
    
    recommended_movies = set()
    for rec_list in all_recommendations:
        recommended_movies.update([movie for movie, _ in rec_list])
    
    return len(recommended_movies) / total_movies if total_movies > 0 else 0.0


def compute_recommendation_metrics(
    recommendations: List[Tuple[str, float]],
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calcule les métriques de qualité pour une liste de recommandations
    """
    diversity = compute_diversity(recommendations)
    novelty = compute_novelty(recommendations)
    
    avg_score = sum([score for _, score in recommendations]) / len(recommendations) if recommendations else 0.0
    max_score = max([score for _, score in recommendations], default=0.0)
    min_score = min([score for _, score in recommendations], default=0.0)
    
    return {
        "diversity": round(diversity, 4),
        "novelty": round(novelty, 4),
        "avg_score": round(avg_score, 4),
        "max_score": round(max_score, 4),
        "min_score": round(min_score, 4),
        "num_recommendations": len(recommendations)
    }


def get_recommendation_statistics(days: int = 7) -> Dict[str, Any]:
    """
    Retourne les statistiques agrégées des recommandations des N derniers jours
    """
    if not os.path.exists(RECOMMENDATIONS_LOG_PATH):
        return {
            "total_recommendations": 0,
            "period_days": days,
            "avg_diversity": 0.0,
            "avg_novelty": 0.0,
            "avg_score": 0.0,
            "methods_used": {}
        }
    
    cutoff_date = datetime.now() - timedelta(days=days)
    all_diversities = []
    all_novelties = []
    all_scores = []
    methods_count = {}
    
    with open(RECOMMENDATIONS_LOG_PATH, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date >= cutoff_date:
                    recs = [(r['movie'], r['score']) for r in entry['recommendations']]
                    metrics = compute_recommendation_metrics(recs)
                    all_diversities.append(metrics['diversity'])
                    all_novelties.append(metrics['novelty'])
                    all_scores.extend([r['score'] for r in entry['recommendations']])
                    method = entry.get('method', 'unknown')
                    methods_count[method] = methods_count.get(method, 0) + 1
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Erreur lors de la lecture d'une entrée du log: {e}")
                continue
    
    return {
        "total_recommendations": len(all_diversities),
        "period_days": days,
        "avg_diversity": round(sum(all_diversities) / len(all_diversities), 4) if all_diversities else 0.0,
        "avg_novelty": round(sum(all_novelties) / len(all_novelties), 4) if all_novelties else 0.0,
        "avg_score": round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0,
        "methods_used": methods_count
    }




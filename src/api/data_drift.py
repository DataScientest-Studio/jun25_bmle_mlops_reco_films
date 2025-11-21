"""
Module pour détecter le Data Drift
Compare les statistiques actuelles avec une référence (baseline)
"""
import logging
import pandas as pd
import psycopg2
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pipeline.config import load_config

logger = logging.getLogger(__name__)

DRIFT_BASELINE_PATH = os.path.join(os.getenv("METRICS_DIR", "metrics"), "drift_baseline.json")

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


def compute_data_statistics(days_back: Optional[int] = None) -> Dict[str, Any]:
    """
    Calcule les statistiques des données
    Si days_back est spécifié, ne considère que les données des N derniers jours
    """
    conn = get_db_connection()
    try:
        if days_back:
            # Convertir days_back en timestamp (approximatif)
            cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
            where_clause = f"WHERE r.timestamp >= {cutoff_timestamp}"
        else:
            where_clause = ""
        
        query = f"""
        SELECT 
            COUNT(DISTINCT r.user_id) as num_users,
            COUNT(DISTINCT r.movie_id) as num_movies,
            COUNT(*) as num_ratings,
            AVG(r.rating) as avg_rating,
            STDDEV(r.rating) as std_rating,
            MIN(r.rating) as min_rating,
            MAX(r.rating) as max_rating,
            COUNT(DISTINCT DATE(to_timestamp(r.timestamp))) as num_days
        FROM ratings r
        {where_clause}
        """
        df = pd.read_sql(query, conn)
        
        if df.empty or df.iloc[0]['num_ratings'] is None:
            return {
                "num_users": 0,
                "num_movies": 0,
                "num_ratings": 0,
                "avg_rating": 0.0,
                "std_rating": 0.0,
                "min_rating": 0.0,
                "max_rating": 0.0,
                "num_days": 0
            }
        
        row = df.iloc[0]
        return {
            "num_users": int(row['num_users']),
            "num_movies": int(row['num_movies']),
            "num_ratings": int(row['num_ratings']),
            "avg_rating": float(row['avg_rating']) if row['avg_rating'] else 0.0,
            "std_rating": float(row['std_rating']) if row['std_rating'] else 0.0,
            "min_rating": float(row['min_rating']) if row['min_rating'] else 0.0,
            "max_rating": float(row['max_rating']) if row['max_rating'] else 0.0,
            "num_days": int(row['num_days']) if row['num_days'] else 0
        }
    finally:
        conn.close()


def save_baseline_statistics() -> Dict[str, Any]:
    """
    Sauvegarde les statistiques actuelles comme baseline pour comparaison future
    """
    stats = compute_data_statistics()
    stats["timestamp"] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(DRIFT_BASELINE_PATH), exist_ok=True)
    with open(DRIFT_BASELINE_PATH, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Baseline sauvegardée: {stats}")
    return stats


def load_baseline_statistics() -> Optional[Dict[str, Any]]:
    """Charge les statistiques baseline depuis le fichier"""
    if not os.path.exists(DRIFT_BASELINE_PATH):
        return None
    
    with open(DRIFT_BASELINE_PATH, 'r') as f:
        return json.load(f)


def detect_drift(
    threshold_pct: float = 10.0,
    baseline: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Détecte le data drift en comparant les statistiques actuelles avec la baseline
    
    Args:
        threshold_pct: Pourcentage de changement acceptable (défaut: 10%)
        baseline: Statistiques de référence (si None, charge depuis fichier)
    
    Returns:
        Dict avec:
        - drift_detected: bool
        - drift_details: dict avec les changements détectés
        - current_stats: statistiques actuelles
        - baseline_stats: statistiques baseline
    """
    current_stats = compute_data_statistics()
    
    if baseline is None:
        baseline = load_baseline_statistics()
    
    if baseline is None:
        # Pas de baseline : sauvegarder les stats actuelles comme baseline
        baseline = save_baseline_statistics()
        return {
            "drift_detected": False,
            "drift_details": {},
            "current_stats": current_stats,
            "baseline_stats": baseline,
            "message": "Aucune baseline trouvée. Statistiques actuelles sauvegardées comme baseline."
        }
    
    drift_details = {}
    drift_detected = False
    
    # Comparer les métriques clés
    metrics_to_check = [
        "avg_rating", "num_users", "num_movies", "num_ratings"
    ]
    
    for metric in metrics_to_check:
        baseline_val = baseline.get(metric, 0)
        current_val = current_stats.get(metric, 0)
        
        if baseline_val == 0:
            continue
        
        change_pct = abs((current_val - baseline_val) / baseline_val * 100)
        
        if change_pct > threshold_pct:
            drift_detected = True
            drift_details[metric] = {
                "baseline": baseline_val,
                "current": current_val,
                "change_pct": round(change_pct, 2),
                "status": "drift_detected"
            }
        else:
            drift_details[metric] = {
                "baseline": baseline_val,
                "current": current_val,
                "change_pct": round(change_pct, 2),
                "status": "normal"
            }
    
    return {
        "drift_detected": drift_detected,
        "drift_details": drift_details,
        "current_stats": current_stats,
        "baseline_stats": baseline,
        "threshold_pct": threshold_pct,
        "message": "Drift détecté" if drift_detected else "Pas de drift détecté"
    }


def get_recent_data_stats(days: int = 7) -> Dict[str, Any]:
    """
    Retourne les statistiques des données récentes (derniers N jours)
    Utile pour détecter des changements récents
    """
    stats = compute_data_statistics(days_back=days)
    stats["period_days"] = days
    return stats


"""
Module pour la détection de drift avec Evidently
"""
import logging
import pandas as pd
import psycopg2
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
from pipeline.config import load_config

try:
    from evidently.report import Report
    from evidently.metrics import DataDriftTable
    from evidently.metric_preset import DataDriftPreset
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    logging.warning("Evidently non disponible. Installation: pip install evidently")

logger = logging.getLogger(__name__)

DRIFT_REPORT_PATH = os.path.join(os.getenv("METRICS_DIR", "metrics"), "evidently_drift_report.json")

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


def load_baseline_data() -> Optional[pd.DataFrame]:
    """Charge les données baseline depuis un fichier"""
    baseline_path = os.path.join(os.getenv("METRICS_DIR", "metrics"), "drift_baseline_data.json")
    if not os.path.exists(baseline_path):
        return None
    
    try:
        with open(baseline_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la baseline: {e}")
        return None


def save_baseline_data(df: pd.DataFrame):
    """Sauvegarde les données baseline"""
    baseline_path = os.path.join(os.getenv("METRICS_DIR", "metrics"), "drift_baseline_data.json")
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    
    # Échantillonner pour éviter des fichiers trop gros
    sample_df = df.sample(n=min(10000, len(df))) if len(df) > 10000 else df
    sample_df.to_json(baseline_path, orient='records', date_format='iso')
    logger.info(f"Baseline data sauvegardee dans {baseline_path}")


def get_current_ratings_sample(n: int = 10000) -> pd.DataFrame:
    """Récupère un échantillon des ratings actuels"""
    conn = get_db_connection()
    try:
        query = f"""
        SELECT user_id, movie_id, rating, timestamp
        FROM ratings
        ORDER BY timestamp DESC
        LIMIT {n}
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


def detect_drift_evidently() -> Dict[str, Any]:
    """
    Détecte le drift avec Evidently
    Retourne un rapport de drift
    """
    if not EVIDENTLY_AVAILABLE:
        return {
            "error": "Evidently non disponible",
            "message": "Installer avec: pip install evidently"
        }
    
    try:
        # Charger les données baseline
        baseline_df = load_baseline_data()
        if baseline_df is None:
            # Créer une baseline avec les données actuelles
            current_df = get_current_ratings_sample()
            save_baseline_data(current_df)
            return {
                "status": "baseline_created",
                "message": "Baseline créée avec les données actuelles"
            }
        
        # Charger les données actuelles
        current_df = get_current_ratings_sample()
        
        # Créer le rapport Evidently
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=baseline_df, current_data=current_df)
        
        # Sauvegarder le rapport
        os.makedirs(os.path.dirname(DRIFT_REPORT_PATH), exist_ok=True)
        report.save_json(DRIFT_REPORT_PATH)
        
        # Extraire les résultats
        drift_detected = False
        drift_metrics = {}
        
        try:
            # Analyser le rapport
            report_dict = report.as_dict()
            for metric_name, metric_result in report_dict.get("metrics", {}).items():
                if "drift" in metric_name.lower() or "number_of_drifted_columns" in metric_name:
                    drift_value = metric_result.get("current", {}).get("number_of_drifted_columns", 0)
                    if drift_value > 0:
                        drift_detected = True
                    drift_metrics[metric_name] = drift_value
        except Exception as e:
            logger.warning(f"Impossible d'analyser le rapport Evidently: {e}")
            # Fallback: utiliser le nombre de colonnes différentes
            if not baseline_df.empty and not current_df.empty:
                if len(baseline_df.columns) != len(current_df.columns):
                    drift_detected = True
        
        return {
            "drift_detected": drift_detected,
            "drift_metrics": drift_metrics,
            "report_path": DRIFT_REPORT_PATH,
            "baseline_size": len(baseline_df),
            "current_size": len(current_df),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection de drift avec Evidently: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors de la détection de drift"
        }


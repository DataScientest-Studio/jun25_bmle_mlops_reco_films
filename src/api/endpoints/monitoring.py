"""
Endpoints pour le monitoring des recommandations et la détection de data drift
"""
import logging
from fastapi import APIRouter, HTTPException
from api.schemas import DriftResponse, MonitoringResponse
from api.data_drift import (
    detect_drift,
    save_baseline_statistics,
    load_baseline_statistics,
    compute_data_statistics,
    get_recent_data_stats
)
from api.monitoring import (
    get_recommendation_statistics,
    compute_recommendation_metrics
)
from api.evidently_drift import detect_drift_evidently
from api.prometheus_metrics import (
    recommendations_total,
    training_runs_total,
    data_drift_detected
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/drift", response_model=DriftResponse)
async def check_data_drift(threshold_pct: float = 10.0, use_evidently: bool = False):
    """
    Vérifie s'il y a du data drift dans les données.
    
    Args:
        threshold_pct: Pourcentage de changement acceptable (défaut: 10%)
        use_evidently: Utiliser Evidently pour la détection (défaut: False)
    
    Returns:
        Informations sur le drift détecté
    """
    try:
        if use_evidently:
            # Utiliser Evidently pour la détection
            evidently_result = detect_drift_evidently()
            if "error" in evidently_result:
                # Fallback vers la méthode basique
                drift_result = detect_drift(threshold_pct=threshold_pct)
            else:
                # Convertir le résultat Evidently au format attendu
                drift_detected = evidently_result.get("drift_detected", False)
                data_drift_detected.set(1 if drift_detected else 0)
                drift_result = {
                    "drift_detected": drift_detected,
                    "drift_details": evidently_result.get("drift_metrics", {}),
                    "current_stats": {"size": evidently_result.get("current_size", 0)},
                    "baseline_stats": {"size": evidently_result.get("baseline_size", 0)},
                    "threshold_pct": threshold_pct,
                    "message": "Drift détecté avec Evidently" if drift_detected else "Pas de drift détecté (Evidently)"
                }
        else:
            # Méthode basique
            drift_result = detect_drift(threshold_pct=threshold_pct)
            data_drift_detected.set(1 if drift_result.get("drift_detected", False) else 0)
        
        return DriftResponse(**drift_result)
    except Exception as e:
        logger.error(f"Erreur lors de la détection de drift: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la détection de drift: {str(e)}"
        )


@router.post("/drift/baseline")
async def create_baseline():
    """
    Crée une nouvelle baseline pour la détection de drift.
    Sauvegarde les statistiques actuelles comme référence.
    """
    try:
        baseline = save_baseline_statistics()
        return {
            "status": "success",
            "message": "Baseline créée avec succès",
            "baseline": baseline
        }
    except Exception as e:
        logger.error(f"Erreur lors de la création de la baseline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de la baseline: {str(e)}"
        )


@router.get("/drift/baseline")
async def get_baseline():
    """
    Récupère la baseline actuelle pour la détection de drift.
    """
    try:
        baseline = load_baseline_statistics()
        if baseline is None:
            return {
                "status": "not_found",
                "message": "Aucune baseline trouvée. Utilisez POST /monitoring/drift/baseline pour en créer une."
            }
        return {
            "status": "found",
            "baseline": baseline
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la baseline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la baseline: {str(e)}"
        )


@router.get("/stats")
async def get_data_statistics(days: int = None):
    """
    Récupère les statistiques des données.
    
    Args:
        days: Si spécifié, retourne les stats des N derniers jours uniquement
    """
    try:
        if days:
            stats = get_recent_data_stats(days=days)
        else:
            stats = compute_data_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.get("/recommendations", response_model=MonitoringResponse)
async def get_recommendation_monitoring(days: int = 7):
    """
    Récupère les statistiques de monitoring des recommandations.
    
    Args:
        days: Nombre de jours à considérer (défaut: 7)
    """
    try:
        stats = get_recommendation_statistics(days=days)
        return MonitoringResponse(**stats)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du monitoring: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du monitoring: {str(e)}"
        )


@router.get("/drift/evidently")
async def check_drift_evidently():
    """
    Vérifie le data drift avec Evidently.
    Retourne un rapport détaillé de drift.
    """
    try:
        result = detect_drift_evidently()
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Erreur lors de la détection de drift avec Evidently: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la détection de drift avec Evidently: {str(e)}"
        )


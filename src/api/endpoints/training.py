"""
Endpoint pour déclencher l'entraînement du modèle
"""
import logging
import traceback
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas import TrainingRequest, TrainingResponse
from pipeline.train_model_pipeline import train_model_mlflow
import mlflow
from pipeline.config import load_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training", tags=["training"])

# État global pour suivre l'entraînement en cours
training_status = {
    "is_training": False,
    "last_run_id": None,
    "last_error": None
}


def run_training():
    """Fonction pour exécuter l'entraînement en arrière-plan"""
    global training_status
    try:
        training_status["is_training"] = True
        training_status["last_error"] = None
        
        logger.info("Demarrage de l'entrainement du modele...")
        
        # Exécuter l'entraînement
        train_model_mlflow()
        
        # Récupérer l'ID de la dernière run MLflow
        config = load_config()
        mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
        mlflow.set_experiment(config["mlflow"]["experiment_name"])
        
        # Récupérer la dernière run
        runs = mlflow.search_runs(order_by=["start_time desc"], max_results=1)
        if not runs.empty:
            training_status["last_run_id"] = runs.iloc[0]["run_id"]
        
        logger.info("Entrainement termine avec succes")
        training_status["is_training"] = False
        
    except Exception as e:
        error_msg = f"Erreur pendant l'entraînement: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        training_status["last_error"] = error_msg
        training_status["is_training"] = False
        raise


@router.post("/", response_model=TrainingResponse)
async def trigger_training(
    request: TrainingRequest = TrainingRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Déclenche l'entraînement du modèle de recommandation.
    
    L'entraînement s'exécute en arrière-plan et peut prendre plusieurs minutes.
    Utilisez GET /training/status pour vérifier le statut.
    """
    global training_status
    
    # Vérifier si un entraînement est déjà en cours
    if training_status["is_training"]:
        raise HTTPException(
            status_code=409,
            detail="Un entraînement est déjà en cours. Attendez qu'il se termine."
        )
    
    try:
        # Ajouter la tâche d'entraînement en arrière-plan
        background_tasks.add_task(run_training)
        
        return TrainingResponse(
            status="started",
            message="L'entraînement a été démarré en arrière-plan. Utilisez GET /training/status pour suivre la progression."
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'entraînement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du démarrage de l'entraînement: {str(e)}"
        )


@router.get("/status", response_model=TrainingResponse)
async def get_training_status():
    """
    Récupère le statut actuel de l'entraînement.
    """
    global training_status
    
    if training_status["is_training"]:
        return TrainingResponse(
            status="training",
            message="L'entraînement est en cours..."
        )
    elif training_status["last_error"]:
        return TrainingResponse(
            status="error",
            message=f"Erreur lors du dernier entraînement: {training_status['last_error']}"
        )
    elif training_status["last_run_id"]:
        # Récupérer les métriques depuis MLflow
        metrics = None
        try:
            config = load_config()
            mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
            run = mlflow.get_run(training_status["last_run_id"])
            metrics = run.data.metrics
        except Exception as e:
            logger.warning(f"Impossible de récupérer les métriques: {e}")
        
        return TrainingResponse(
            status="completed",
            message="Dernier entraînement terminé avec succès",
            run_id=training_status["last_run_id"],
            metrics=metrics
        )
    else:
        return TrainingResponse(
            status="idle",
            message="Aucun entraînement n'a été effectué"
        )


import logging
import os
import pandas as pd
import joblib
import psycopg2
from functools import lru_cache
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas import PredictionRequest, PredictionResponse, MovieRecommendation, BatchPredictionRequest, BatchPredictionResponse
from pipeline.config import load_config
from surprise import Dataset, Reader
from pipeline.predict_model_pipeline import top_n_user, predict_model_mlflow
from api.cold_start import is_new_user, get_cold_start_recommendations
from api.monitoring import log_recommendation, compute_recommendation_metrics
from api.prometheus_metrics import recommendations_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["predict"])


@lru_cache(maxsize=1)
def load_model_and_data():
    logger.info("Chargement du modèle et des données en mémoire...")
    config = load_config()
    
    # Chemins
    model_path = os.path.join(config["model"]["model_dir"], config["model"]["model_filename"])
    
    # Vérifier que le modèle existe
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Le modèle n'existe pas à {model_path}. "
            "Veuillez d'abord entraîner le modèle via POST /training/"
        )
    
    # Charger le modèle
    model = joblib.load(model_path)
    
    # Charger les données depuis PostgreSQL
    conn = psycopg2.connect(
        dbname=config["db"]["dbname"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )
    
    # Charger les ratings
    ratings_df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)
    
    # Charger les films
    movies_df = pd.read_sql("SELECT movie_id, title FROM movies", conn)
    
    # Fermer la connexion
    conn.close()
    
    # Préparer le dataset Surprise
    predict_sample_size = config["predict"]["predict_sample_size"]
    if predict_sample_size < len(ratings_df):
        ratings_sample = ratings_df.sample(n=predict_sample_size, random_state=42)
    else:
        ratings_sample = ratings_df
    
    reader = Reader(rating_scale=(0.5, 5))
    df_surprise = Dataset.load_from_df(ratings_sample[['user_id', 'movie_id', 'rating']], reader)
    trainset = df_surprise.build_full_trainset()
    
    return model, trainset, movies_df


@router.post("/", response_model=PredictionResponse)
async def get_recommendations(request: PredictionRequest):
    """
    Obtient les recommandations de films pour un utilisateur donné.
    
    Gère automatiquement le cold start pour les nouveaux utilisateurs.
    Retourne les top N films recommandés pour l'utilisateur spécifié.
    """
    try:
        # Vérifier si l'utilisateur est nouveau (cold start)
        if is_new_user(request.user_id):
            logger.info(f"Utilisateur {request.user_id} est nouveau, utilisation de cold start")
            top_n = get_cold_start_recommendations(request.user_id, N=request.top_n)
            method = "cold_start"
        else:
            # Charger le modèle et les données
            model, trainset, movies_df = load_model_and_data()
            
            # Obtenir les recommandations avec le modèle
            top_n = top_n_user(
                algo=model,
                trainset=trainset,
                movies_df=movies_df,
                user_id=request.user_id,
                N=request.top_n
            )
            method = "collaborative_filtering"
            
            # Si pas de recommandations (utilisateur dans trainset mais pas de prédictions)
            if not top_n:
                logger.warning(f"Pas de recommandations pour utilisateur {request.user_id}, fallback vers cold start")
                top_n = get_cold_start_recommendations(request.user_id, N=request.top_n)
                method = "cold_start_fallback"
        
        if not top_n:
            raise HTTPException(
                status_code=404,
                detail=f"Impossible de générer des recommandations pour l'utilisateur {request.user_id}."
            )
        
        # Convertir en format de réponse
        recommendations = [
            MovieRecommendation(movie=movie, score=score)
            for movie, score in top_n
        ]
        
        top_score = max([score for _, score in top_n], default=None)
        
        # Logger la recommandation pour monitoring
        try:
            log_recommendation(request.user_id, top_n, method=method)
            # Incrémenter le compteur Prometheus
            recommendations_total.inc(len(recommendations))
        except Exception as e:
            logger.warning(f"Erreur lors du logging de la recommandation: {e}")
        
        # Sauvegarder automatiquement en CSV + MLflow
        try:
            import mlflow
            import os
            
            # Créer le dossier predictions si nécessaire
            os.makedirs("predictions", exist_ok=True)
            
            # Sauvegarder en CSV
            results_df = pd.DataFrame(top_n, columns=['movie', 'score'])
            csv_path = f"./predictions/top_{request.top_n}_user_{request.user_id}.csv"
            results_df.to_csv(csv_path, index=False)
            
            # Logger dans MLflow
            config = load_config()
            mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
            mlflow.set_experiment(config["mlflow"]["experiment_name"])
            
            with mlflow.start_run(run_name=f"Prediction_User_{request.user_id}"):
                mlflow.log_param("user_id", request.user_id)
                mlflow.log_param("top_n", request.top_n)
                mlflow.log_param("method", method)
                mlflow.log_metric("top_score", top_score if top_score else 0.0)
                mlflow.log_artifact(csv_path)
            
            logger.info(f"Prédictions sauvegardées: {csv_path}")
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde MLflow: {e}")
        
        return PredictionResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            top_score=top_score
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations: {str(e)}"
        )


@router.get("/health")
async def predict_health():
    """Vérifie que le service de prédiction est opérationnel"""
    try:
        model, trainset, movies_df = load_model_and_data()
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_path": os.path.join(
                load_config()["model"]["model_dir"],
                load_config()["model"]["model_filename"]
            )
        }
    except FileNotFoundError:
        return {
            "status": "model_not_found",
            "model_loaded": False,
            "message": "Le modèle n'a pas encore été entraîné"
        }
    except Exception as e:
        return {
            "status": "error",
            "model_loaded": False,
            "error": str(e)
        }


@router.post("/batch", response_model=BatchPredictionResponse)
async def run_batch_predictions(request: BatchPredictionRequest):
    """
    Exécute des prédictions batch pour plusieurs utilisateurs.
    
    Sauvegarde les résultats en CSV dans le dossier predictions/
    et log les artefacts dans MLflow.
    """
    try:
        import mlflow
        
        # Exécuter le pipeline de prédiction batch
        predict_model_mlflow(users_id=request.user_ids, N=request.top_n)
        
        # Récupérer le run_id de la dernière exécution
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(load_config()["mlflow"]["experiment_name"])
        if experiment:
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"],
                max_results=1
            )
            run_id = runs[0].info.run_id if runs else None
        else:
            run_id = None
        
        return BatchPredictionResponse(
            status="success",
            message=f"Prédictions batch générées pour {len(request.user_ids)} utilisateurs",
            users_processed=len(request.user_ids),
            predictions_dir="./predictions",
            mlflow_run_id=run_id
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Modèle non trouvé: {str(e)}. Veuillez d'abord entraîner le modèle."
        )
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des prédictions batch: {str(e)}"
        )

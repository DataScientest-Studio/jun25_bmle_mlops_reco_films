"""
Endpoint pour obtenir des recommandations de films
"""
import logging
import os
import pandas as pd
import joblib
import psycopg2
from fastapi import APIRouter, HTTPException
from api.schemas import PredictionRequest, PredictionResponse, MovieRecommendation
from pipeline.config import load_config
from surprise import Dataset, Reader
from pipeline.predict_model_pipeline import top_n_user
from api.cold_start import is_new_user, get_cold_start_recommendations
from api.monitoring import log_recommendation, compute_recommendation_metrics
from api.prometheus_metrics import recommendations_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["predict"])


def load_model_and_data():
    """Charge le modèle et les données nécessaires pour les prédictions"""
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


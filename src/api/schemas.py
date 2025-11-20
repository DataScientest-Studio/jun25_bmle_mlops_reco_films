"""
Schémas Pydantic pour les requêtes et réponses de l'API
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TrainingRequest(BaseModel):
    """Schéma pour la requête d'entraînement"""
    force: bool = Field(
        default=False,
        description="Forcer l'entraînement même si un modèle récent existe"
    )


class TrainingResponse(BaseModel):
    """Schéma pour la réponse d'entraînement"""
    status: str = Field(description="Statut de l'entraînement")
    message: str = Field(description="Message descriptif")
    run_id: Optional[str] = Field(default=None, description="ID de la run MLflow")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Métriques du modèle")


class PredictionRequest(BaseModel):
    """Schéma pour la requête de prédiction"""
    user_id: int = Field(description="ID de l'utilisateur")
    top_n: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Nombre de recommandations à retourner (1-50)"
    )


class MovieRecommendation(BaseModel):
    """Schéma pour une recommandation de film"""
    movie: str = Field(description="Titre du film")
    score: float = Field(description="Score de prédiction")


class PredictionResponse(BaseModel):
    """Schéma pour la réponse de prédiction"""
    user_id: int = Field(description="ID de l'utilisateur")
    recommendations: List[MovieRecommendation] = Field(description="Liste des recommandations")
    top_score: Optional[float] = Field(default=None, description="Meilleur score")


class HealthResponse(BaseModel):
    """Schéma pour la réponse de santé de l'API"""
    status: str = Field(description="Statut de l'API")
    version: str = Field(description="Version de l'API")


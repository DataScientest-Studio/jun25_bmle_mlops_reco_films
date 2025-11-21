"""
Tests unitaires pour l'API
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.app import app

client = TestClient(app)


def test_health_endpoint():
    """Test de l'endpoint de santé"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test de l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_training_status_endpoint():
    """Test de l'endpoint de statut d'entraînement"""
    response = client.get("/training/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] in ["idle", "training", "completed", "error"]


def test_predict_endpoint_validation():
    """Test de validation de l'endpoint de prédiction"""
    # Test avec user_id manquant
    response = client.post("/predict/", json={"top_n": 5})
    assert response.status_code == 422  # Validation error
    
    # Test avec top_n invalide
    response = client.post("/predict/", json={"user_id": 1, "top_n": 0})
    assert response.status_code == 422
    
    # Test avec top_n trop élevé
    response = client.post("/predict/", json={"user_id": 1, "top_n": 100})
    assert response.status_code == 422


def test_monitoring_drift_endpoint():
    """Test de l'endpoint de détection de drift"""
    response = client.get("/monitoring/drift?threshold_pct=10.0")
    assert response.status_code == 200
    data = response.json()
    assert "drift_detected" in data
    assert "current_stats" in data
    assert "baseline_stats" in data or data.get("message", "").startswith("Aucune baseline")


def test_monitoring_stats_endpoint():
    """Test de l'endpoint de statistiques"""
    response = client.get("/monitoring/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "statistics" in data
    stats = data["statistics"]
    assert "num_users" in stats
    assert "num_movies" in stats
    assert "num_ratings" in stats


def test_monitoring_recommendations_endpoint():
    """Test de l'endpoint de monitoring des recommandations"""
    response = client.get("/monitoring/recommendations?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "total_recommendations" in data
    assert "avg_diversity" in data
    assert "avg_novelty" in data
    assert "methods_used" in data


def test_data_generate_ratings_endpoint():
    """Test de l'endpoint de génération de ratings"""
    response = client.post("/generate-ratings?batch_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "count" in data


def test_predict_health_endpoint():
    """Test de l'endpoint de santé de prédiction"""
    response = client.get("/predict/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


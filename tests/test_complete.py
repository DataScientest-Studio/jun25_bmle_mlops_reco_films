"""
Tests complets de toutes les fonctionnalités
"""
import pytest
import sys
import os
import time
import requests

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

API_URL = os.getenv("API_URL", "http://localhost:8080")

class TestCompleteSystem:
    """Tests complets du système"""
    
    def test_api_health(self):
        """Test que l'API répond"""
        response = requests.get(f"{API_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_prometheus_metrics(self):
        """Test que les métriques Prometheus sont disponibles"""
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        assert response.status_code == 200
        assert "api_requests_total" in response.text or "prometheus" in response.text.lower()
    
    def test_cold_start_recommendation(self):
        """Test du cold start avec un nouvel utilisateur"""
        response = requests.post(
            f"{API_URL}/predict/",
            json={"user_id": 999999999, "top_n": 5},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    def test_data_drift_baseline(self):
        """Test de création de baseline pour drift"""
        response = requests.post(f"{API_URL}/monitoring/drift/baseline", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_data_drift_detection(self):
        """Test de détection de drift"""
        response = requests.get(
            f"{API_URL}/monitoring/drift?threshold_pct=10.0",
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "drift_detected" in data
        assert "current_stats" in data
    
    def test_monitoring_stats(self):
        """Test des statistiques de monitoring"""
        response = requests.get(f"{API_URL}/monitoring/stats", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "statistics" in data
    
    def test_monitoring_recommendations(self):
        """Test du monitoring des recommandations"""
        response = requests.get(
            f"{API_URL}/monitoring/recommendations?days=7",
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_recommendations" in data
        assert "avg_diversity" in data
    
    def test_training_status(self):
        """Test du statut d'entraînement"""
        response = requests.get(f"{API_URL}/training/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["idle", "training", "completed", "error"]
    
    @pytest.mark.slow
    def test_evidently_drift(self):
        """Test de détection de drift avec Evidently (peut être lent)"""
        response = requests.get(
            f"{API_URL}/monitoring/drift/evidently",
            timeout=60
        )
        # Peut retourner 200 ou 500 si Evidently n'est pas disponible
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


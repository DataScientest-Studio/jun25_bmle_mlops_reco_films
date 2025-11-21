"""
Tests pour le module Data Drift
"""
import pytest
import sys
import os
import json
import tempfile
import shutil

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.data_drift import (
    compute_data_statistics,
    save_baseline_statistics,
    load_baseline_statistics,
    detect_drift
)


def test_compute_data_statistics():
    """Test de calcul des statistiques"""
    stats = compute_data_statistics()
    assert "num_users" in stats
    assert "num_movies" in stats
    assert "num_ratings" in stats
    assert "avg_rating" in stats
    assert isinstance(stats["num_users"], int)
    assert isinstance(stats["num_movies"], int)
    assert isinstance(stats["num_ratings"], int)
    assert isinstance(stats["avg_rating"], (int, float))


def test_save_and_load_baseline():
    """Test de sauvegarde et chargement de baseline"""
    # Sauvegarder une baseline
    baseline = save_baseline_statistics()
    assert baseline is not None
    assert "timestamp" in baseline
    
    # Charger la baseline
    loaded = load_baseline_statistics()
    assert loaded is not None
    assert loaded["timestamp"] == baseline["timestamp"]


def test_detect_drift():
    """Test de détection de drift"""
    # Créer une baseline d'abord
    save_baseline_statistics()
    
    # Détecter le drift
    result = detect_drift(threshold_pct=10.0)
    assert "drift_detected" in result
    assert "drift_details" in result
    assert "current_stats" in result
    assert "baseline_stats" in result
    assert isinstance(result["drift_detected"], bool)


"""
Tests pour le module Cold Start
"""
import pytest
import sys
import os

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.cold_start import (
    is_new_user,
    is_new_movie,
    get_popular_movies,
    get_cold_start_recommendations
)


def test_get_popular_movies():
    """Test de récupération des films populaires"""
    movies = get_popular_movies(N=5)
    assert len(movies) <= 5
    assert all(isinstance(movie, tuple) for movie in movies)
    assert all(len(movie) == 2 for movie in movies)  # (title, score)
    assert all(isinstance(movie[1], (int, float)) for movie in movies)


def test_get_cold_start_recommendations():
    """Test de génération de recommandations cold start"""
    # Utiliser un ID très élevé pour être sûr que l'utilisateur n'existe pas
    recommendations = get_cold_start_recommendations(user_id=999999999, N=5)
    assert len(recommendations) <= 5
    assert all(isinstance(rec, tuple) for rec in recommendations)
    assert all(len(rec) == 2 for rec in recommendations)
    assert all(isinstance(rec[1], (int, float)) for rec in recommendations)


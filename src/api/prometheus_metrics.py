"""
Module pour les métriques Prometheus
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Compteurs pour les requêtes
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

# Histogramme pour la latence
api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Gauge pour les recommandations
recommendations_total = Gauge(
    'recommendations_total',
    'Total number of recommendations generated'
)

# Gauge pour les entraînements
training_runs_total = Gauge(
    'training_runs_total',
    'Total number of training runs'
)

# Gauge pour le drift détecté
data_drift_detected = Gauge(
    'data_drift_detected',
    'Data drift detection status (1 = detected, 0 = not detected)'
)

def get_metrics():
    """Retourne les métriques Prometheus"""
    return Response(content=generate_latest(), media_type="text/plain")


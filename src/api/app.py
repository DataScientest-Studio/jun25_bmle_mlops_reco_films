"""
Application FastAPI principale pour l'API de recommandation de films
"""
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from api.endpoints import training, predict, data, monitoring
from api.schemas import HealthResponse
from api.prometheus_metrics import (
    api_requests_total,
    api_request_duration_seconds,
    get_metrics
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="Movie Recommendation API",
    description="API pour le système de recommandation de films",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS (pour permettre les requêtes depuis le frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour les métriques Prometheus
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Enregistrer les métriques
    endpoint = request.url.path
    method = request.method
    status = response.status_code
    
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    return response

# Inclure les routers
app.include_router(training.router)
app.include_router(predict.router)
app.include_router(data.router)
app.include_router(monitoring.router)

# Endpoint pour les métriques Prometheus
@app.get("/metrics")
async def metrics():
    """Endpoint pour les métriques Prometheus"""
    return get_metrics()


@app.get("/", response_model=HealthResponse)
async def root():
    """
    Endpoint racine pour vérifier que l'API est opérationnelle.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Endpoint de santé pour vérifier le statut de l'API.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


"""
Application FastAPI principale pour l'API de recommandation de films
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import training, predict, data
from api.schemas import HealthResponse

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

# Inclure les routers
app.include_router(training.router)
app.include_router(predict.router)
app.include_router(data.router)


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


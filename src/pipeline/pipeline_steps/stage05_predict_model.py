#!/usr/bin/env python3
import logging
from pipeline.predict_model_pipeline import predict_model_mlflow

if __name__ == "__main__":
    # Configuration du logging
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    logger.info("🎯 Lancement des prédictions du modèle...")

    # Appel de la fonction principale pour effectuer les prédictions
    predict_model_mlflow()  # users_id=None → utilisera [1] par défaut

    logger.info("✅ Prédictions terminées.")

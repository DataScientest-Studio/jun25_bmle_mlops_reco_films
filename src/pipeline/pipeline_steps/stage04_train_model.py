#!/usr/bin/env python3
import logging
from pipeline.train_model_pipeline import train_model_mlflow

if __name__ == "__main__":
    # Configuration du logging
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    logger.info("🏋️ Lancement de l'entraînement du modèle...")

    # Appel de la fonction principale pour entraîner le modèle
    train_model_mlflow()

    logger.info("✅ Entraînement du modèle terminé.")

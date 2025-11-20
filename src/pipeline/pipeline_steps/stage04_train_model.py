#!/usr/bin/env python3
import logging
from pipeline.train_model_pipeline import train_model_mlflow

if __name__ == "__main__":
    # Configuration du logging
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    logger.info("Lancement de l'entrainement du modele (donnees depuis PostgreSQL)...")

    try:
        # Appel de la fonction principale
        train_model_mlflow()
        logger.info("Entrainement du modele termine avec succes.")
    except Exception as e:
        logger.error(f"Erreur pendant l'entrainement : {e}")
        raise  # Relance l'erreur pour que DVC la capture

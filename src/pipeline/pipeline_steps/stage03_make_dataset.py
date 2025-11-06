#!/usr/bin/env python3
import logging

# Imports corrects depuis le package pipeline
from pipeline.make_dataset_pipeline import make_dataset_pipeline
from pipeline.config import load_config

if __name__ == "__main__":
    # Configuration du logging
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    # Charger la configuration
    config = load_config()
    input_filepath = config["make_dataset"]["input_dir"]
    output_filepath = config["make_dataset"]["output_dir"]

    logger.info(f"📥 Lecture des données depuis : {input_filepath}")
    logger.info(f"📤 Sauvegarde des données traitées dans : {output_filepath}")

    # Appel de la fonction principale
    make_dataset_pipeline(input_filepath, output_filepath)

    logger.info("✅ Étape Make Dataset terminée.")

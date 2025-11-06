#!/usr/bin/env python3
import logging
from pipeline.import_data_pipeline import import_raw_data

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # Appel de la fonction d'import
    import_raw_data()

    logger = logging.getLogger(__name__)
    logger.info("✅ Raw data downloaded and ready.")

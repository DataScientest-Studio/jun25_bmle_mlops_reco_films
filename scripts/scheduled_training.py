#!/usr/bin/env python3
"""
Script pour l'entraînement planifié du modèle
Peut être exécuté via cron ou manuellement
"""
import sys
import os
import logging
import requests
from datetime import datetime

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8080")

def trigger_training():
    """Déclenche l'entraînement via l'API"""
    try:
        logger.info(f"Déclenchement de l'entraînement planifié à {datetime.now()}")
        
        response = requests.post(
            f"{API_URL}/training/",
            json={"force": False},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Entraînement déclenché avec succès")
            logger.info(f"Réponse: {response.json()}")
            return True
        else:
            logger.error(f"Erreur lors du déclenchement: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion à l'API: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = trigger_training()
    sys.exit(0 if success else 1)


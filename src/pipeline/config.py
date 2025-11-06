import os
import yaml

def load_config(config_path=None):

    if config_path is None:
        # Chemin par défaut relatif à ce fichier config.py
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    config_path = os.path.abspath(config_path)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Le fichier de configuration n'existe pas : {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config

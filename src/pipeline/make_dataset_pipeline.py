import logging
from pathlib import Path
from pipeline.config import load_config


def make_dataset_pipeline(input_filepath: str, output_filepath: str):
    """
    Transforme les données depuis input_filepath vers output_filepath.
    
    - Crée le dossier de sortie si nécessaire
    - Copie tous les fichiers CSV (à adapter selon ta logique)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Making final dataset from raw data: {input_filepath} -> {output_filepath}")

    input_path = Path(input_filepath)
    output_path = Path(output_filepath)
    output_path.mkdir(parents=True, exist_ok=True)

    for csv_file in input_path.glob("*.csv"):
        target_file = output_path / csv_file.name
        target_file.write_text(csv_file.read_text())
        logger.info(f"Copied {csv_file} -> {target_file}")


def main():
    # Configuration du logging
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # Charger la configuration
    config = load_config()
    input_filepath = config["make_dataset"]["input_dir"]
    output_filepath = config["make_dataset"]["output_dir"]

    # Exécuter la pipeline
    make_dataset_pipeline(input_filepath, output_filepath)


if __name__ == "__main__":
    main()

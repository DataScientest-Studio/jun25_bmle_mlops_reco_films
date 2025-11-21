import os
import time
import requests
from pipeline.check_structure_pipeline import check_structure_pipeline

def download_file(bucket_folder_url, filename, raw_data_relative_path, max_retries=5, timeout=30):
    """Télécharge un fichier depuis le bucket S3 avec retries."""
    output_file = os.path.join(raw_data_relative_path, filename)
    if os.path.isfile(output_file):
        print(f"File {output_file} already exists. Skipping download.")
        return

    object_url = f"{bucket_folder_url.rstrip('/')}/{filename}"

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Downloading {object_url} -> {output_file} (attempt {attempt})")
            response = requests.get(object_url, timeout=timeout)
            response.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"Successfully downloaded {filename}")
            return
        except (requests.RequestException, IOError) as e:
            print(f"Attempt {attempt} failed for {filename}: {e}")
            if attempt < max_retries:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise RuntimeError(f"Failed to download {filename} after {max_retries} attempts")

def import_raw_data(raw_data_relative_path="./data/raw",
                    filenames=None,
                    bucket_folder_url="https://mlops-project-db.s3.eu-west-1.amazonaws.com/movie_recommandation/"):
    """
    Télécharge les fichiers depuis le bucket S3 dans le dossier raw_data_relative_path
    avec retries et timeout.
    """
    if filenames is None:
        filenames = [
            "genome-scores.csv", "genome-tags.csv", "links.csv",
            "movies.csv", "ratings.csv", "README.txt", "tags.csv"
        ]

    # Vérifie/crée le dossier raw_data_relative_path
    check_structure_pipeline(folders=[raw_data_relative_path])

    # Télécharge tous les fichiers
    for filename in filenames:
        download_file(bucket_folder_url, filename, raw_data_relative_path)

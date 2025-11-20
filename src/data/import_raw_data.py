import os
import requests
from pipeline.check_structure_pipeline import check_structure_pipeline


def import_raw_data(
    raw_data_relative_path=None,
    filenames=None,
    bucket_folder_url="https://mlops-project-db.s3.eu-west-1.amazonaws.com/movie_recommandation/"
):
    """
    Télécharge les fichiers depuis le bucket S3 dans le dossier data/raw (à la racine du projet)
    Compatible avec une exécution locale ou dans un conteneur Docker.
    """

    # 📁 Détection de la racine du projet (2 niveaux au-dessus du script actuel)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    # 📂 Par défaut, le dossier cible est data/raw à la racine
    if raw_data_relative_path is None:
        raw_data_relative_path = os.path.join(project_root, "data", "raw")

    print(f"📂 Dossier cible : {raw_data_relative_path}")

    if filenames is None:
        filenames = [
            "genome-scores.csv",
            "genome-tags.csv",
            "links.csv",
            "movies.csv",
            "ratings.csv",
            "README.txt",
            "tags.csv"
        ]

    # Vérifie/crée le dossier raw_data_relative_path
    check_structure_pipeline(folders=[raw_data_relative_path])

    for filename in filenames:
        output_file = os.path.join(raw_data_relative_path, filename)

        # ✅ Si le fichier existe déjà, on ne le télécharge pas
        if os.path.isfile(output_file):
            print(f"ℹ️ Fichier {output_file} déjà présent. Téléchargement ignoré.")
            continue

        # ✅ Construction propre de l’URL
        object_url = f"{bucket_folder_url.rstrip('/')}/{filename}"
        print(f"⬇️ Téléchargement de {object_url} -> {output_file}")

        try:
            response = requests.get(object_url, timeout=30)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"✅ {filename} téléchargé avec succès.")
            else:
                print(f"❌ Erreur {response.status_code} lors de l'accès à {object_url}")
        except requests.RequestException as e:
            print(f"⚠️ Erreur réseau : {e}")

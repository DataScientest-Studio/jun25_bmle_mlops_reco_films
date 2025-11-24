# src/pipeline/models_module_def/predict_model_pipeline.py
# -------------------------------

import os
import json
import pandas as pd
import joblib
import mlflow
import psycopg2
from surprise import Dataset, Reader
from pipeline.config import load_config

# Charger la configuration
config = load_config()


def top_n_user(algo, trainset, movies_df, user_id, N=5):
    """Renvoie le top N des recommandations pour un utilisateur donné."""
    try:
        inner_uid = trainset.to_inner_uid(user_id)
    except ValueError:
        print(f"L'utilisateur {user_id} n'existe pas dans l'echantillon.")
        return []

    # Récupérer les items déjà notés par l'utilisateur
    rated_items = {trainset.to_raw_iid(i) for (i, _) in trainset.ur[inner_uid]}

    # Créer l'anti-testset
    anti_testset = [
        (user_id, trainset.to_raw_iid(i), trainset.global_mean)
        for i in trainset.all_items()
        if trainset.to_raw_iid(i) not in rated_items
    ]

    # Prédictions
    preds = algo.test(anti_testset)

    # Sélection du top N
    top_n = sorted(preds, key=lambda x: x.est, reverse=True)[:N]

    # Récupérer les titres des films
    movie_index = movies_df.set_index('movie_id')
    return [
        (movie_index.loc[p.iid, 'title'], p.est)
        for p in top_n
        if p.iid in movie_index.index
    ]


def predict_model_mlflow(users_id=None, N=5, predict_sample_size=2_000_000):
    """Exécute la prédiction pour un ou plusieurs utilisateurs et logge sur MLflow."""
    # Configurer les credentials AWS/MinIO pour boto3 (forcer la configuration)
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")
    os.environ["AWS_DEFAULT_REGION"] = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")

    # Chemins
    model_path = os.path.join(config["model"]["model_dir"], config["model"]["model_filename"])

    # Créer les dossiers de sortie si inexistants
    os.makedirs("predictions", exist_ok=True)
    os.makedirs("metrics", exist_ok=True)

    # Configuration MLflow
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # Charger le modèle
    best_svd = joblib.load(model_path)
    
    # Charger les données depuis PostgreSQL
    conn = psycopg2.connect(
        dbname=config["db"]["dbname"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )
    
    # Charger les ratings
    ratings_df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)
    
    # Charger les films
    movies_df = pd.read_sql("SELECT movie_id, title FROM movies", conn)
    
    # Fermer la connexion
    conn.close()

    # Échantillonnage des ratings si nécessaire
    if predict_sample_size < len(ratings_df):
        ratings_sample = ratings_df.sample(n=predict_sample_size, random_state=42)
    else:
        ratings_sample = ratings_df

    # Préparer le dataset Surprise
    reader = Reader(rating_scale=(0.5, 5))
    df_surprise = Dataset.load_from_df(ratings_sample[['user_id', 'movie_id', 'rating']], reader)
    trainset = df_surprise.build_full_trainset()

    # Utilisateur par défaut
    if users_id is None:
        users_id = [1]

    all_metrics = {}

    # Démarrer une session MLflow
    with mlflow.start_run(run_name="Predictions"):
        mlflow.log_param("model_path", model_path)
        mlflow.log_param("ratings_sample_size", len(ratings_sample))
        mlflow.log_param("top_N", N)

        for user_id in users_id:
            # Top N recommandations
            top_n = top_n_user(best_svd, trainset, movies_df, user_id=user_id, N=N)

            # Sauvegarder les résultats
            results_df = pd.DataFrame(top_n, columns=['movie', 'score'])
            results_path = f"./predictions/top_{N}_user_{user_id}.csv"
            results_df.to_csv(results_path, index=False)
            mlflow.log_artifact(results_path)

            # Affichage
            print(f"\nTop {N} recommandations pour l'utilisateur {user_id} :")
            for title, score in top_n:
                print(f"{title} → {score:.2f}")

            # Stocker la meilleure note pour le JSON des métriques
            all_metrics[f"user_{user_id}_top_score"] = max([s for _, s in top_n], default=None)

        # Sauvegarder les métriques dans un fichier JSON
        metrics_path = "./metrics/predict_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(all_metrics, f, indent=4)
        mlflow.log_artifact(metrics_path)
        print(f"\nMetriques sauvegardees dans {metrics_path}")

if __name__ == "__main__":
    predict_model_mlflow()

# src/pipeline/models_module_def/predict_model_pipeline_local.py
# -------------------------------

import os
import json
import pandas as pd
import joblib
from surprise import Dataset, Reader
from pipeline.config import load_config

# Charger la configuration
config = load_config()


def top_n_user(algo, trainset, movies_df, user_id, N=5):
    """Renvoie le top N des recommandations pour un utilisateur donné."""
    try:
        inner_uid = trainset.to_inner_uid(user_id)
    except ValueError:
        print(f"⚠️ L'utilisateur {user_id} n'existe pas dans l'échantillon.")
        return []

    # Items déjà notés par l'utilisateur
    rated_items = {trainset.to_raw_iid(i) for (i, _) in trainset.ur[inner_uid]}

    # Anti-testset
    anti_testset = [
        (user_id, trainset.to_raw_iid(i), trainset.global_mean)
        for i in trainset.all_items()
        if trainset.to_raw_iid(i) not in rated_items
    ]

    # Prédictions
    preds = algo.test(anti_testset)

    # Top N
    top_n = sorted(preds, key=lambda x: x.est, reverse=True)[:N]

    movie_index = movies_df.set_index('movieId')
    return [
        (movie_index.loc[p.iid, 'title'], p.est)
        for p in top_n
        if p.iid in movie_index.index
    ]


def predict_model_local(users_id=None, N=5, predict_sample_size=2_000_000):
    """Exécute la prédiction pour un ou plusieurs utilisateurs (local, sans MLflow)."""

    # Chemins
    model_path = os.path.join(config["model"]["model_dir"], config["model"]["model_filename"])
    ratings_path = os.path.join(config["data"]["raw_dir"], config["features"]["ratings_file"])
    movies_path = os.path.join(config["data"]["raw_dir"], config["features"]["movies_file"])

    # Créer dossiers de sortie si inexistants
    os.makedirs("predictions", exist_ok=True)
    os.makedirs("metrics", exist_ok=True)

    # Charger modèle et données
    best_svd = joblib.load(model_path)
    ratings_df = pd.read_csv(ratings_path, usecols=['userId', 'movieId', 'rating'])
    movies_df = pd.read_csv(movies_path)

    # Échantillonnage
    if predict_sample_size < len(ratings_df):
        ratings_sample = ratings_df.sample(n=predict_sample_size, random_state=42)
    else:
        ratings_sample = ratings_df

    # Dataset Surprise
    reader = Reader(rating_scale=(0.5, 5))
    df_surprise = Dataset.load_from_df(ratings_sample[['userId', 'movieId', 'rating']], reader)
    trainset = df_surprise.build_full_trainset()

    # Utilisateur par défaut
    if users_id is None:
        users_id = [1]

    all_metrics = {}

    for user_id in users_id:
        top_n = top_n_user(best_svd, trainset, movies_df, user_id=user_id, N=N)

        # Sauvegarder les résultats
        results_df = pd.DataFrame(top_n, columns=['movie', 'score'])
        results_path = f"./predictions/top_{N}_user_{user_id}.csv"
        results_df.to_csv(results_path, index=False)

        # Affichage
        print(f"\nTop {N} recommandations pour l'utilisateur {user_id} :")
        for title, score in top_n:
            print(f"{title} → {score:.2f}")

        # Stocker la meilleure note pour le JSON des métriques
        all_metrics[f"user_{user_id}_top_score"] = max([s for _, s in top_n], default=None)

    # Sauvegarder les métriques
    metrics_path = "./metrics/predict_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=4)

    print(f"\n💾 Métriques sauvegardées dans {metrics_path}")


if __name__ == "__main__":

    predict_model_local(users_id=[1, 2], N=5, predict_sample_size=500_000)

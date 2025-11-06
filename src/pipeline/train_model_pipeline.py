# -------------------------------
# src/pipeline/models_module_def/train_model_pipeline.py
# -------------------------------
import os
from pipeline.config import load_config
import pandas as pd
import joblib
import json
import mlflow
import mlflow.sklearn
from surprise import Dataset, Reader, SVD, KNNBasic, NormalPredictor
from surprise.model_selection import cross_validate, GridSearchCV

# Charger config
config = load_config()

def train_model_mlflow():
    # Chemins et paramètres
    ratings_path = os.path.join(config["data"]["raw_dir"], config["features"]["ratings_file"])
    movies_path = os.path.join(config["data"]["raw_dir"], config["features"]["movies_file"])
    model_dir = config["model"]["model_dir"]
    os.makedirs(model_dir, exist_ok=True)
    
    sample_size = 500_000
    knn_sample_size = config["model"]["n_neighbors"] * 2500
    train_sample_size = 1_000_000

    # MLflow
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # -------------------------------
    # Charger les données et filtrer
    # -------------------------------
    ratings_df = pd.read_csv(ratings_path, usecols=['userId','movieId','rating'])
    movies_df = pd.read_csv(movies_path)

    # Filtrage
    min_ratings_user = 50
    min_ratings_movie = 100
    active_users = ratings_df.groupby('userId').size()
    active_users = active_users[active_users >= min_ratings_user].index
    ratings_df = ratings_df[ratings_df['userId'].isin(active_users)]

    popular_movies = ratings_df.groupby('movieId').size()
    popular_movies = popular_movies[popular_movies >= min_ratings_movie].index
    ratings_df = ratings_df[ratings_df['movieId'].isin(popular_movies)]

    print("Shape après filtrage :", ratings_df.shape)
    reader = Reader(rating_scale=(0.5, 5))

    # -------------------------------
    # Datasets pour comparaison
    # -------------------------------
    df_sample = ratings_df.sample(n=sample_size, random_state=42)
    df_surprise_sample = Dataset.load_from_df(df_sample[['userId','movieId','rating']], reader)

    df_knn_sample = ratings_df.sample(n=knn_sample_size, random_state=42)
    df_surprise_knn = Dataset.load_from_df(df_knn_sample[['userId','movieId','rating']], reader)

    # -------------------------------
    # MLflow run
    # -------------------------------
    with mlflow.start_run(run_name="Model_Comparison_and_Training"):

        mlflow.log_param("min_ratings_user", min_ratings_user)
        mlflow.log_param("min_ratings_movie", min_ratings_movie)
        mlflow.log_param("sample_size", sample_size)
        mlflow.log_param("knn_sample_size", knn_sample_size)

        # Dictionnaire pour stocker toutes les métriques
        all_metrics = {}

        # Évaluer modèles
        models = {
            "SVD": SVD(n_factors=12, random_state=42),
            "KNNBasic": KNNBasic(k=config["model"]["n_neighbors"], sim_options={'name': 'cosine', 'user_based': False}),
            "RandomBaseline": NormalPredictor()
        }

        for name, model in models.items():
            print(f"\n🔹 Évaluation du modèle : {name}")
            if name == "KNNBasic":
                results = cross_validate(model, df_surprise_knn, measures=['RMSE','MAE'], cv=3, verbose=False)
            else:
                results = cross_validate(model, df_surprise_sample, measures=['RMSE','MAE'], cv=3, verbose=False)

            rmse = results['test_rmse'].mean()
            mae = results['test_mae'].mean()
            print(f"{name} → RMSE: {rmse:.4f}, MAE: {mae:.4f}")
            mlflow.log_metric(f"{name}_RMSE", rmse)
            mlflow.log_metric(f"{name}_MAE", mae)

            # Stocker pour fichier JSON
            all_metrics[f"{name}_RMSE"] = rmse
            all_metrics[f"{name}_MAE"] = mae

        # GridSearch SVD
        param_grid = {'n_factors':[12,20], 'lr_all':[0.002,0.005], 'reg_all':[0.02,0.05]}
        gs = GridSearchCV(SVD, param_grid, measures=['rmse','mae'], cv=3)
        gs.fit(df_surprise_sample)

        best_params = gs.best_params['rmse']
        best_rmse = gs.best_score['rmse']
        print("\n✅ Meilleurs paramètres SVD :", best_params)
        print("RMSE :", best_rmse)
        mlflow.log_params(best_params)
        mlflow.log_metric("SVD_best_RMSE", best_rmse)
        all_metrics["SVD_best_RMSE"] = best_rmse

        # -------------------------------
        # Entraîner sur échantillon plus grand
        # -------------------------------
        df_train_sample = ratings_df.sample(n=train_sample_size, random_state=42)
        full_df_surprise = Dataset.load_from_df(df_train_sample[['userId','movieId','rating']], reader)
        trainset = full_df_surprise.build_full_trainset()

        best_svd = gs.best_estimator['rmse']
        best_svd.fit(trainset)
        print(f"✅ SVD entraîné sur {train_sample_size} lignes")

        # -------------------------------
        # Sauvegarde modèle et métriques
        # -------------------------------
        model_path = os.path.join(model_dir, config["model"]["model_filename"])
        joblib.dump(best_svd, model_path)
        mlflow.log_artifact(model_path)
        mlflow.sklearn.log_model(best_svd, artifact_path="best_svd_model")
        print(f"💾 Modèle sauvegardé dans {model_path}")

        # Sauvegarder métriques localement pour DVC
        os.makedirs("metrics", exist_ok=True)
        metrics_path = os.path.join("metrics", "train_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(all_metrics, f, indent=4)
        mlflow.log_artifact(metrics_path)
        print(f"💾 Métriques sauvegardées dans {metrics_path}")
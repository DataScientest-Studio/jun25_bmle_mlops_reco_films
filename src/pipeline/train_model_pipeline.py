# -------------------------------
# src/pipeline/models_module_def/train_model_pipeline.py
# -------------------------------
import os
import psycopg2
from psycopg2 import sql
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
    # Configurer les credentials AWS/MinIO pour boto3 (forcer la configuration)
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")
    os.environ["AWS_DEFAULT_REGION"] = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
    
    # Chemins et paramètres
    model_dir = config["model"]["model_dir"]
    os.makedirs(model_dir, exist_ok=True)
    
    sample_size = 500_000
    knn_sample_size = config["model"]["n_neighbors"] * 2500
    train_sample_size = 1_000_000

    # Paramètres de filtrage
    min_ratings_user = 50
    min_ratings_movie = 100    

    # MLflow
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # -------------------------------
    # Charger les données depuis PostgreSQL et filtrer
    # -------------------------------
    conn = psycopg2.connect(
        dbname=config["db"]["dbname"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )

    # Requête pour récupérer les ratings filtrés (avec échantillonnage aléatoire)
    query_ratings = sql.SQL("""
        WITH
        active_users AS (
            SELECT user_id
            FROM ratings
            GROUP BY user_id
            HAVING COUNT(*) >= {min_ratings_user}
        ),
        popular_movies AS (
            SELECT movie_id
            FROM ratings
            GROUP BY movie_id
            HAVING COUNT(*) >= {min_ratings_movie}
        )
        SELECT r.user_id, r.movie_id, r.rating
        FROM ratings r
        JOIN active_users au ON r.user_id = au.user_id
        JOIN popular_movies pm ON r.movie_id = pm.movie_id
    """).format(
        min_ratings_user=sql.Literal(min_ratings_user),
        min_ratings_movie=sql.Literal(min_ratings_movie)
    )

    # Charger les données filtrées
    # Conversion de l'objet sql.Composed en string pour pandas
    ratings_df = pd.read_sql(query_ratings.as_string(conn), conn)
    print("Shape après filtrage SQL :", ratings_df.shape)

    # Fermer la connexion
    conn.close()

    # -------------------------------
    # Échantillonnage aléatoire (sans random_state pour varier les échantillons)
    # -------------------------------
    reader = Reader(rating_scale=(0.5, 5))
    df_sample = ratings_df.sample(n=sample_size)  # Échantillon aléatoire différent à chaque fois
    df_surprise_sample = Dataset.load_from_df(df_sample[['user_id','movie_id','rating']], reader)
    df_knn_sample = ratings_df.sample(n=knn_sample_size)  # Échantillon aléatoire différent à chaque fois
    df_surprise_knn = Dataset.load_from_df(df_knn_sample[['user_id','movie_id','rating']], reader)
    
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
            print(f"\nEvaluation du modele : {name}")
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
        print("\nMeilleurs parametres SVD :", best_params)
        print("RMSE :", best_rmse)
        mlflow.log_params(best_params)
        mlflow.log_metric("SVD_best_RMSE", best_rmse)
        all_metrics["SVD_best_RMSE"] = best_rmse

        # -------------------------------
        # Entraîner sur échantillon plus grand
        # -------------------------------
        df_train_sample = ratings_df.sample(n=train_sample_size, random_state=42)
        full_df_surprise = Dataset.load_from_df(df_train_sample[['user_id','movie_id','rating']], reader)
        trainset = full_df_surprise.build_full_trainset()

        best_svd = gs.best_estimator['rmse']
        best_svd.fit(trainset)
        print(f"SVD entraine sur {train_sample_size} lignes")

        # -------------------------------
        # Sauvegarde modèle et métriques
        # -------------------------------
        model_path = os.path.join(model_dir, config["model"]["model_filename"])
        joblib.dump(best_svd, model_path)
        mlflow.log_artifact(model_path)
        mlflow.sklearn.log_model(best_svd, artifact_path="best_svd_model")
        print(f"Modele sauvegarde dans {model_path}")

        # Sauvegarder métriques localement pour DVC
        os.makedirs("metrics", exist_ok=True)
        metrics_path = os.path.join("metrics", "train_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(all_metrics, f, indent=4)
        mlflow.log_artifact(metrics_path)
        print(f"Metriques sauvegardees dans {metrics_path}")
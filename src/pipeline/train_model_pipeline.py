import pandas as pd
import mlflow
import mlflow.sklearn
from surprise import Dataset, Reader, SVD, KNNBasic, NormalPredictor
from surprise.model_selection import cross_validate
import joblib
import os
from src.pipeline.data_loader import load_filtered_ratings
import logging

logger = logging.getLogger(__name__)


def train_model_mlflow(force=False):
    from api.endpoints.training import training_status
    
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
    mlflow.set_experiment("Film_Recommendation_Experiment")

    sample_size = 100000 
    knn_sample_size = 20000
    train_sample_size = 200000
    min_ratings_user = 50
    min_ratings_movie = 100
    
    training_status["progress"] = "Chargement des données..."
    ratings_df = load_filtered_ratings(min_ratings_user=min_ratings_user, min_ratings_movie=min_ratings_movie)

    from pipeline.config import load_config
    config = load_config()
    model_dir = config["model"]["model_dir"]
    model_filename = config["model"]["model_filename"]
    model_path = os.path.join(model_dir, model_filename)
    
    available_rows = len(ratings_df)
    actual_sample_size = min(sample_size, available_rows)
    actual_knn_sample_size = min(knn_sample_size, available_rows)
    actual_train_sample_size = min(train_sample_size, available_rows)
    
    reader = Reader(rating_scale=(0.5, 5))
    
    df_sample = ratings_df.sample(n=actual_sample_size)
    df_surprise_sample = Dataset.load_from_df(df_sample[['user_id','movie_id','rating']], reader)
    
    df_knn_sample = ratings_df.sample(n=actual_knn_sample_size)
    df_surprise_knn = Dataset.load_from_df(df_knn_sample[['user_id','movie_id','rating']], reader)

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        logger.info(f"MLflow run démarrée: {run_id}")
        
        mlflow.log_param("original_sample_size", sample_size)
        mlflow.log_param("original_knn_sample_size", knn_sample_size)
        mlflow.log_param("original_train_sample_size", train_sample_size)
        mlflow.log_param("actual_sample_size", actual_sample_size)
        mlflow.log_param("actual_knn_sample_size", actual_knn_sample_size)
        mlflow.log_param("actual_train_sample_size", actual_train_sample_size)
        mlflow.log_param("available_rows_after_filter", available_rows)
        mlflow.log_param("min_ratings_user", min_ratings_user)
        mlflow.log_param("min_ratings_movie", min_ratings_movie)
        mlflow.log_param("force_training", force)

        training_status["progress"] = "Entraînement SVD..."
        model_svd = SVD()
        cv_svd = cross_validate(model_svd, df_surprise_sample, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_svd = cv_svd['test_rmse'].mean()
        mlflow.log_metric("svd_rmse", mean_rmse_svd)

        training_status["progress"] = "Entraînement KNNBasic..."
        model_knn = KNNBasic()
        cv_knn = cross_validate(model_knn, df_surprise_knn, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_knn = cv_knn['test_rmse'].mean()
        mlflow.log_metric("knn_rmse", mean_rmse_knn)

        training_status["progress"] = "Entraînement NormalPredictor..."
        model_dummy = NormalPredictor()
        cv_dummy = cross_validate(model_dummy, df_surprise_sample, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_dummy = cv_dummy['test_rmse'].mean()
        mlflow.log_metric("dummy_rmse", mean_rmse_dummy)

        best_rmse = min(mean_rmse_svd, mean_rmse_knn, mean_rmse_dummy)
        
        client = mlflow.tracking.MlflowClient()
        experiment_id = client.get_experiment_by_name("Film_Recommendation_Experiment").experiment_id
        runs = client.search_runs(experiment_id, order_by=["metrics.best_rmse ASC"], max_results=1)
        
        previous_best_rmse = None
        if runs:
            previous_best_rmse = runs[0].data.metrics.get("best_rmse")

        is_best_model = False
        model_exists = os.path.exists(model_path)

        if previous_best_rmse is None or best_rmse < previous_best_rmse:
            is_best_model = True
        elif not model_exists:
            pass
        elif force:
            pass

        mlflow.log_metric("best_rmse", best_rmse)
        mlflow.log_param("is_best_model", is_best_model)

        if is_best_model or not model_exists or force:
            if best_rmse == mean_rmse_svd:
                best_algo = SVD()
                best_algo_name = "SVD"
            elif best_rmse == mean_rmse_knn:
                best_algo = KNNBasic()
                best_algo_name = "KNNBasic"
            else:
                best_algo = NormalPredictor()
                best_algo_name = "NormalPredictor"
            
            mlflow.log_param("best_algorithm", best_algo_name)
            
            train_df = ratings_df.sample(n=actual_train_sample_size)
            train_set = Dataset.load_from_df(train_df[['user_id','movie_id','rating']], reader).build_full_trainset()
            best_algo.fit(train_set)
            
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(best_algo, model_path)
            mlflow.log_artifact(model_path)
            
            mlflow.sklearn.log_model(
                sk_model=best_algo,
                artifact_path="model",
                registered_model_name="Best_Film_Recommender"
            )
        
        return run_id

if __name__ == "__main__":
    train_model_mlflow()
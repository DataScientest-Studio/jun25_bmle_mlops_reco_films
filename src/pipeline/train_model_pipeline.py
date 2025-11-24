import pandas as pd
import mlflow
import mlflow.sklearn
from surprise import Dataset, Reader, SVD, KNNBasic, NormalPredictor
from surprise.model_selection import cross_validate
import joblib
import os
from src.pipeline.data_loader import load_filtered_ratings
import os
from src.pipeline.data_loader import load_filtered_ratings
import logging

logger = logging.getLogger(__name__)


def train_model_mlflow():
    # Import du training_status pour mettre à jour la progression
    from api.endpoints.training import training_status
    
    # Configuration MLflow
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
    mlflow.set_experiment("Film_Recommendation_Experiment")

    # Paramètres
    sample_size = 100000 
    knn_sample_size = 20000
    train_sample_size = 200000
    min_ratings_user = 50
    min_ratings_movie = 100
    
    # Charger les données via le module dédié
    training_status["progress"] = "Chargement des données..."
    ratings_df = load_filtered_ratings(min_ratings_user=min_ratings_user, min_ratings_movie=min_ratings_movie)
    print("Shape après filtrage SQL :", ratings_df.shape)

    # -------------------------------
    # Ajuster les tailles d'échantillon en fonction des données disponibles
    # -------------------------------
    available_rows = len(ratings_df)
    actual_sample_size = min(sample_size, available_rows)
    actual_knn_sample_size = min(knn_sample_size, available_rows)
    actual_train_sample_size = min(train_sample_size, available_rows)
    
    print(f"Tailles d'échantillon ajustées:")
    print(f"  Sample size: {actual_sample_size} (demandé: {sample_size})")
    print(f"  KNN sample size: {actual_knn_sample_size} (demandé: {knn_sample_size})")
    print(f"  Train sample size: {actual_train_sample_size} (demandé: {train_sample_size})")

    # -------------------------------
    # Échantillonnage aléatoire
    # -------------------------------
    reader = Reader(rating_scale=(0.5, 5))
    
    # Échantillon pour l'évaluation rapide
    df_sample = ratings_df.sample(n=actual_sample_size)
    df_surprise_sample = Dataset.load_from_df(df_sample[['user_id','movie_id','rating']], reader)
    
    # Échantillon pour KNN (plus petit car coûteux en mémoire)
    df_knn_sample = ratings_df.sample(n=actual_knn_sample_size)
    df_surprise_knn = Dataset.load_from_df(df_knn_sample[['user_id','movie_id','rating']], reader)

    with mlflow.start_run() as run:
        # Capturer le run_id pour le retourner
        run_id = run.info.run_id
        logger.info(f"MLflow run démarrée: {run_id}")
        
        # Log des paramètres
        mlflow.log_param("original_sample_size", sample_size)
        mlflow.log_param("original_knn_sample_size", knn_sample_size)
        mlflow.log_param("original_train_sample_size", train_sample_size)
        mlflow.log_param("actual_sample_size", actual_sample_size)
        mlflow.log_param("actual_knn_sample_size", actual_knn_sample_size)
        mlflow.log_param("actual_train_sample_size", actual_train_sample_size)
        mlflow.log_param("available_rows_after_filter", available_rows)
        mlflow.log_param("min_ratings_user", min_ratings_user)
        mlflow.log_param("min_ratings_movie", min_ratings_movie)

        # 1. SVD
        training_status["progress"] = "Entraînement SVD..."
        print("Entraînement SVD...")
        model_svd = SVD()
        cv_svd = cross_validate(model_svd, df_surprise_sample, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_svd = cv_svd['test_rmse'].mean()
        mlflow.log_metric("svd_rmse", mean_rmse_svd)
        print(f"SVD RMSE: {mean_rmse_svd}")

        # 2. KNNBasic
        training_status["progress"] = "Entraînement KNNBasic..."
        print("Entraînement KNNBasic...")
        model_knn = KNNBasic()
        cv_knn = cross_validate(model_knn, df_surprise_knn, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_knn = cv_knn['test_rmse'].mean()
        mlflow.log_metric("knn_rmse", mean_rmse_knn)
        print(f"KNN RMSE: {mean_rmse_knn}")

        # 3. NormalPredictor (Baseline)
        training_status["progress"] = "Entraînement NormalPredictor..."
        print("Entraînement NormalPredictor...")
        model_dummy = NormalPredictor()
        cv_dummy = cross_validate(model_dummy, df_surprise_sample, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        mean_rmse_dummy = cv_dummy['test_rmse'].mean()
        mlflow.log_metric("dummy_rmse", mean_rmse_dummy)
        print(f"Dummy RMSE: {mean_rmse_dummy}")

        # Comparaison et sauvegarde du meilleur modèle
        best_rmse = min(mean_rmse_svd, mean_rmse_knn, mean_rmse_dummy)
        
        # Récupérer le meilleur RMSE précédent
        client = mlflow.tracking.MlflowClient()
        experiment_id = client.get_experiment_by_name("Film_Recommendation_Experiment").experiment_id
        runs = client.search_runs(experiment_id, order_by=["metrics.best_rmse ASC"], max_results=1)
        
        previous_best_rmse = None
        if runs:
            previous_best_rmse = runs[0].data.metrics.get("best_rmse")

        print(f"Meilleur RMSE actuel : {best_rmse}")
        print(f"Meilleur RMSE précédent : {previous_best_rmse}")

        is_best_model = False
        if previous_best_rmse is None or best_rmse < previous_best_rmse:
            is_best_model = True
            print("Nouveau meilleur modèle trouvé !")
        else:
            print("Le modèle actuel n'est pas meilleur que le précédent.")

        mlflow.log_metric("best_rmse", best_rmse)
        mlflow.log_param("is_best_model", is_best_model)

        # Réentraîner le meilleur modèle sur un plus grand jeu de données (si possible)
        if is_best_model:
            print("Réentraînement du meilleur modèle sur le jeu d'entraînement...")
            
            # Sélection du meilleur algorithme
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
            
            # Entraînement final
            train_df = ratings_df.sample(n=actual_train_sample_size)
            train_set = Dataset.load_from_df(train_df[['user_id','movie_id','rating']], reader).build_full_trainset()
            best_algo.fit(train_set)
            
            # Sauvegarde
            os.makedirs("models", exist_ok=True)
            model_path = "models/best_svd_model.pkl"
            joblib.dump(best_algo, model_path)
            mlflow.log_artifact(model_path)
            
            # Enregistrement dans le Model Registry
            mlflow.sklearn.log_model(
                sk_model=best_algo,
                artifact_path="model",
                registered_model_name="Best_Film_Recommender"
            )
            print(f"Modèle {best_algo_name} sauvegardé et enregistré.")
        else:
            print("Pas de sauvegarde de modèle car pas d'amélioration.")
        
        # Retourner le run_id
        return run_id

if __name__ == "__main__":
    train_model_mlflow()
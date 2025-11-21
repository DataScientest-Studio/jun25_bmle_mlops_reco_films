# -------------------------------
# Importer les librairies
# -------------------------------
import os
import pandas as pd
from surprise import Dataset, Reader, SVD, KNNBasic, NormalPredictor
from surprise.model_selection import cross_validate, GridSearchCV
import joblib

# -------------------------------
# Charger les donnees et filtrer
# -------------------------------
ratings_path = "./data/raw/ratings.csv"
movies_path = "./data/raw/movies.csv"

ratings_df = pd.read_csv(ratings_path, usecols=['userId','movieId','rating'])
movies_df = pd.read_csv(movies_path)

# Filtrage utilisateurs et films
min_ratings_user = 50
min_ratings_movie = 100

active_users = ratings_df.groupby('userId').size()
active_users = active_users[active_users >= min_ratings_user].index
ratings_df = ratings_df[ratings_df['userId'].isin(active_users)]

popular_movies = ratings_df.groupby('movieId').size()
popular_movies = popular_movies[popular_movies >= min_ratings_movie].index
ratings_df = ratings_df[ratings_df['movieId'].isin(popular_movies)]

print("Shape après filtrage :", ratings_df.shape)

# -------------------------------
# Creer Dataset Surprise pour cross-validation rapide
# -------------------------------
reader = Reader(rating_scale=(0.5, 5))

# Échantillon pour SVD et RandomBaseline
sample_size = min(500_000, len(ratings_df))
df_sample = ratings_df.sample(n=sample_size, random_state=42)
df_surprise_sample = Dataset.load_from_df(df_sample[['userId','movieId','rating']], reader)

# Échantillon réduit pour KNNUserBased pour éviter OOM
knn_user_sample_size = min(10_000, len(ratings_df))
df_knn_user_sample = ratings_df.sample(n=knn_user_sample_size, random_state=42)
df_surprise_knn_user = Dataset.load_from_df(df_knn_user_sample[['userId','movieId','rating']], reader)

# Échantillon pour KNNItemBased
knn_item_sample_size = min(50_000, len(ratings_df))
df_knn_item_sample = ratings_df.sample(n=knn_item_sample_size, random_state=42)
df_surprise_knn_item = Dataset.load_from_df(df_knn_item_sample[['userId','movieId','rating']], reader)

# -------------------------------
# Cross-validation rapide pour comparer modeles
# -------------------------------
models = {
    "SVD": (SVD(n_factors=12, random_state=42), df_surprise_sample),
    "RandomBaseline": (NormalPredictor(), df_surprise_sample),
    "KNNItemBased": (KNNBasic(k=20, sim_options={'name':'cosine','user_based':False}), df_surprise_knn_item),
    "KNNUserBased": (KNNBasic(k=20, sim_options={'name':'cosine','user_based':True}), df_surprise_knn_user)
}

for name, (model, dataset) in models.items():
    print(f"\n🔹 Évaluation modèle : {name}")
    cross_validate(model, dataset, measures=['RMSE','MAE'], cv=3, verbose=True)

# -------------------------------
# GridSearchCV rapide pour SVD
# -------------------------------
param_grid = {
    'n_factors': [12, 20],
    'lr_all': [0.002, 0.005],
    'reg_all': [0.02, 0.05]
}

gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3)
gs.fit(df_surprise_sample)

print("\nMeilleurs parametres SVD :", gs.best_params['rmse'])
print("RMSE :", gs.best_score['rmse'])

# -------------------------------
# Entrainer le meilleur SVD sur un sous-echantillon
# -------------------------------
train_sample_size = min(1_000_000, len(ratings_df))
df_train_sample = ratings_df.sample(n=train_sample_size, random_state=42)

full_df_surprise = Dataset.load_from_df(df_train_sample[['userId','movieId','rating']], reader)
trainset = full_df_surprise.build_full_trainset()

best_svd = gs.best_estimator['rmse']
best_svd.fit(trainset)
print(f"SVD entraine sur {train_sample_size} lignes")

# -------------------------------
# Sauvegarder le modele entraine
# -------------------------------
os.makedirs("./models", exist_ok=True)
joblib.dump(best_svd, "./models/best_svd_model.pkl")
print("Modele sauvegarde dans ./models/best_svd_model.pkl")

print("\nEntrainement termine avec succes")

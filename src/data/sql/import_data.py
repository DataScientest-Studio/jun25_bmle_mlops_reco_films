import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from tqdm import tqdm
import re
import sys

# Configuration de la connexion à PostgreSQL
db_config = {
    "host": "db",
    "database": "reco_films",
    "user": "reco_films",
    "password": "reco_films",
}

# Chemin des fichiers CSV
csv_paths = {
    "movies": "/csv/movies.csv",
    "ratings": "/csv/ratings.csv",
    "tags": "/csv/tags.csv",
    "links": "/csv/links.csv",
    "genome_tags": "/csv/genome-tags.csv",
    "genome_scores": "/csv/genome-scores.csv",
}

def extract_year(title):
    match = re.search(r'\((\d{4})\)', title)
    if match:
        return int(match.group(1))
    return None

def import_data():
    # Connexion à PostgreSQL
    engine = create_engine(f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

    # Import des films
    print("Import des films...")
    movies_df = pd.read_csv(csv_paths["movies"])
    movies_df["release_year"] = movies_df["title"].apply(extract_year)
    movies_df = movies_df.rename(columns={"movieId": "movie_id", "title": "title"})
    movies_df = movies_df[["movie_id", "title", "release_year"]]
    movies_df.to_sql("movies", engine, if_exists="append", index=False)

    # Import des utilisateurs à partir des ratings (en chunks)
    print("Import des utilisateurs...")
    user_ids = set()
    for chunk in tqdm(pd.read_csv(csv_paths["ratings"], chunksize=50000), 
                      desc="Lecture ratings.csv",
                      unit="chunks",
                      mininterval=1,
                      dynamic_ncols=True,
                      file=sys.stdout):
        user_ids.update(chunk["userId"].unique())
    users_df = pd.DataFrame({"user_id": list(user_ids)})
    users_df.to_sql("users", engine, if_exists="append", index=False)

    # Import des évaluations (en chunks)
    print("Import des évaluations...")
    for chunk in tqdm(pd.read_csv(csv_paths["ratings"], chunksize=50000), 
                      desc="Import ratings → DB",
                      unit="chunks",
                      mininterval=1,
                      dynamic_ncols=True,
                      file=sys.stdout):
        chunk = chunk.rename(columns={"userId": "user_id", "movieId": "movie_id"})
        chunk.to_sql("ratings", engine, if_exists="append", index=False)

    # Import des tags (en chunks)
    print("Import des tags...")
    unique_tags = set()
    for chunk in tqdm(pd.read_csv(csv_paths["tags"], chunksize=50000), 
                      desc="Lecture tags.csv",
                      unit="chunks",
                      mininterval=1,
                      dynamic_ncols=True,
                      file=sys.stdout):
        unique_tags.update(chunk["tag"].dropna().unique())
    unique_tags_df = pd.DataFrame({"tag": list(unique_tags)})
    unique_tags_df.to_sql("tags", engine, if_exists="append", index=False)

    # Import des liens
    print("Import des liens...")
    links_df = pd.read_csv(csv_paths["links"])
    links_df = links_df.rename(columns={"movieId": "movie_id", "imdbId": "imdb_id", "tmdbId": "tmdb_id"})
    links_df.to_sql("links", engine, if_exists="append", index=False)

    # Import des genome_tags
    print("Import des genome_tags...")
    genome_tags_df = pd.read_csv(csv_paths["genome_tags"])
    genome_tags_df = genome_tags_df.rename(columns={"tagId": "tag_id"})
    genome_tags_df.to_sql("genome_tags", engine, if_exists="append", index=False)

    # Import des genome_scores (en chunks)
    print("Import des genome_scores...")
    for chunk in tqdm(pd.read_csv(csv_paths["genome_scores"], chunksize=100000), 
                      desc="Import genome_scores → DB",
                      unit="chunks",
                      mininterval=1,
                      dynamic_ncols=True,
                      file=sys.stdout):
        chunk = chunk.rename(columns={"movieId": "movie_id", "tagId": "tag_id"})          
        chunk.to_sql("genome_scores", engine, if_exists="append", index=False)

    # Import des movie_genres
    print("Import des movie_genres...")
    movies_df_full = pd.read_csv(csv_paths["movies"])
    movies_df_full["genres"] = movies_df_full["genres"].str.split("|")
    movie_genres_records = []
    for _, row in movies_df_full.iterrows():
        for genre in row["genres"]:
            movie_genres_records.append({"movie_id": row["movieId"], "genre": genre})

    movie_genres_df = pd.DataFrame(movie_genres_records)
    genres_df = pd.DataFrame({"name": movie_genres_df["genre"].unique()})
    genres_df.to_sql("genres", engine, if_exists="append", index=False)

    # Mise à jour des IDs de genres
    genres_df = pd.read_sql("SELECT genre_id, name FROM genres", engine)
    movie_genres_df = movie_genres_df.merge(genres_df, left_on="genre", right_on="name")
    movie_genres_df = movie_genres_df[["movie_id", "genre_id"]]
    movie_genres_df.to_sql("movie_genres", engine, if_exists="append", index=False)

    # Import des movie_tags (en chunks)
    print("Import des movie_tags...")
    # Récupère les correspondances tag → tag_id
    tags_mapping = pd.read_sql("SELECT tag_id, tag FROM tags", engine)
    tags_mapping_dict = dict(zip(tags_mapping["tag"], tags_mapping["tag_id"]))

    for i, chunk in enumerate(tqdm(pd.read_csv(csv_paths["tags"], chunksize=50000),
                                   desc="Import movie_tags → DB",
                                   unit="chunks",
                                   mininterval=1,
                                   dynamic_ncols=True,
                                   file=sys.stdout)):
        # Renomme les colonnes
        chunk = chunk.rename(columns={"userId": "user_id", "movieId": "movie_id"})
        # Filtre les lignes où le tag existe dans la table tags
        chunk = chunk[chunk["tag"].isin(tags_mapping_dict.keys())]
        # Ajoute la colonne tag_id
        chunk["tag_id"] = chunk["tag"].map(tags_mapping_dict)
        # Sélectionne les colonnes nécessaires
        chunk = chunk[["user_id", "movie_id", "tag_id", "timestamp"]]
        # Insère dans la base de données
        chunk.to_sql("movie_tags", engine, if_exists="append", index=False)

    print("Import terminé avec succès !")

if __name__ == "__main__":
    import_data()

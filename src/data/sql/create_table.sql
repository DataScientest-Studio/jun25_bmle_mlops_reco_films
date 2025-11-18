-- Création de la table 'genres'
CREATE TABLE IF NOT EXISTS genres (
    genre_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Création de la table 'movies'
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    release_year INTEGER
);

-- Création de la table de liaison 'movie_genres'
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- Création de la table 'users'
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
);

-- Création de la table 'ratings'
CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating DECIMAL(2, 1) NOT NULL CHECK (rating >= 0.5 AND rating <= 5.0),
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (user_id, movie_id)
);

-- Création de la table 'tags'
CREATE TABLE IF NOT EXISTS tags (
    tag_id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL
);

-- Création de la table de liaison 'movie_tags'
CREATE TABLE IF NOT EXISTS movie_tags (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE,
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (user_id, movie_id, tag_id)
);

-- Création de la table 'genome_tags'
CREATE TABLE IF NOT EXISTS genome_tags (
    tag_id INTEGER PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL
);

-- Création de la table 'genome_scores'
CREATE TABLE IF NOT EXISTS genome_scores (
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES genome_tags(tag_id) ON DELETE CASCADE,
    relevance DECIMAL(10, 6) NOT NULL,
    PRIMARY KEY (movie_id, tag_id)
);

-- Création de la table 'links'
CREATE TABLE IF NOT EXISTS links (
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    imdb_id VARCHAR(20),
    tmdb_id VARCHAR(20),
    PRIMARY KEY (movie_id)
);

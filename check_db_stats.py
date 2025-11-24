#!/usr/bin/env python3
"""Script pour vérifier les statistiques de la base de données PostgreSQL"""
import psycopg2
from psycopg2 import sql

# Configuration de la connexion
DB_CONFIG = {
    "dbname": "mlops_db",
    "user": "mlops_user",
    "password": "mlops_password",
    "host": "localhost",
    "port": 5432
}

def check_database_stats():
    """Vérifie les statistiques de la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
        print("=" * 70)
        
        # 1. Nombre total de ratings
        cursor.execute("SELECT COUNT(*) FROM ratings;")
        total_ratings = cursor.fetchone()[0]
        print(f"\n✅ Nombre total de ratings: {total_ratings:,}")
        
        # 2. Nombre d'utilisateurs uniques
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM ratings;")
        total_users = cursor.fetchone()[0]
        print(f"✅ Nombre d'utilisateurs uniques: {total_users:,}")
        
        # 3. Nombre de films uniques
        cursor.execute("SELECT COUNT(DISTINCT movie_id) FROM ratings;")
        total_movies = cursor.fetchone()[0]
        print(f"✅ Nombre de films uniques: {total_movies:,}")
        
        # 4. Distribution des notes par utilisateur
        cursor.execute("""
            SELECT 
                COUNT(*) as num_users,
                CASE 
                    WHEN rating_count < 10 THEN '< 10 notes'
                    WHEN rating_count < 50 THEN '10-49 notes'
                    WHEN rating_count < 100 THEN '50-99 notes'
                    WHEN rating_count < 500 THEN '100-499 notes'
                    ELSE '500+ notes'
                END as category
            FROM (
                SELECT user_id, COUNT(*) as rating_count
                FROM ratings
                GROUP BY user_id
            ) user_stats
            GROUP BY category
            ORDER BY 
                CASE category
                    WHEN '< 10 notes' THEN 1
                    WHEN '10-49 notes' THEN 2
                    WHEN '50-99 notes' THEN 3
                    WHEN '100-499 notes' THEN 4
                    ELSE 5
                END;
        """)
        print("\n📈 Distribution des utilisateurs par nombre de notes:")
        for count, category in cursor.fetchall():
            print(f"   {category:20s}: {count:,} utilisateurs")
        
        # 5. Distribution des notes par film
        cursor.execute("""
            SELECT 
                COUNT(*) as num_movies,
                CASE 
                    WHEN rating_count < 10 THEN '< 10 notes'
                    WHEN rating_count < 50 THEN '10-49 notes'
                    WHEN rating_count < 100 THEN '50-99 notes'
                    WHEN rating_count < 500 THEN '100-499 notes'
                    ELSE '500+ notes'
                END as category
            FROM (
                SELECT movie_id, COUNT(*) as rating_count
                FROM ratings
                GROUP BY movie_id
            ) movie_stats
            GROUP BY category
            ORDER BY 
                CASE category
                    WHEN '< 10 notes' THEN 1
                    WHEN '10-49 notes' THEN 2
                    WHEN '50-99 notes' THEN 3
                    WHEN '100-499 notes' THEN 4
                    ELSE 5
                END;
        """)
        print("\n📈 Distribution des films par nombre de notes:")
        for count, category in cursor.fetchall():
            print(f"   {category:20s}: {count:,} films")
        
        # 6. Simulation des filtres actuels
        print("\n" + "=" * 70)
        print("🔍 IMPACT DES FILTRES ACTUELS (min_user=50, min_movie=100)")
        print("=" * 70)
        
        cursor.execute("""
            WITH
            active_users AS (
                SELECT user_id
                FROM ratings
                GROUP BY user_id
                HAVING COUNT(*) >= 50
            ),
            popular_movies AS (
                SELECT movie_id
                FROM ratings
                GROUP BY movie_id
                HAVING COUNT(*) >= 100
            )
            SELECT COUNT(*) as filtered_ratings
            FROM ratings r
            JOIN active_users au ON r.user_id = au.user_id
            JOIN popular_movies pm ON r.movie_id = pm.movie_id;
        """)
        filtered_ratings = cursor.fetchone()[0]
        print(f"\n✅ Ratings après filtrage: {filtered_ratings:,}")
        print(f"📉 Pourcentage conservé: {(filtered_ratings/total_ratings*100):.2f}%")
        
        # 7. Utilisateurs et films après filtrage
        cursor.execute("""
            WITH
            active_users AS (
                SELECT user_id
                FROM ratings
                GROUP BY user_id
                HAVING COUNT(*) >= 50
            )
            SELECT COUNT(*) FROM active_users;
        """)
        filtered_users = cursor.fetchone()[0]
        print(f"✅ Utilisateurs après filtrage (≥50 notes): {filtered_users:,}")
        
        cursor.execute("""
            WITH
            popular_movies AS (
                SELECT movie_id
                FROM ratings
                GROUP BY movie_id
                HAVING COUNT(*) >= 100
            )
            SELECT COUNT(*) FROM popular_movies;
        """)
        filtered_movies = cursor.fetchone()[0]
        print(f"✅ Films après filtrage (≥100 notes): {filtered_movies:,}")
        
        # 8. Suggestions de filtres alternatifs
        print("\n" + "=" * 70)
        print("💡 SUGGESTIONS DE FILTRES ALTERNATIFS")
        print("=" * 70)
        
        for min_user, min_movie in [(10, 20), (20, 50), (30, 75)]:
            cursor.execute(f"""
                WITH
                active_users AS (
                    SELECT user_id
                    FROM ratings
                    GROUP BY user_id
                    HAVING COUNT(*) >= {min_user}
                ),
                popular_movies AS (
                    SELECT movie_id
                    FROM ratings
                    GROUP BY movie_id
                    HAVING COUNT(*) >= {min_movie}
                )
                SELECT COUNT(*) as filtered_ratings
                FROM ratings r
                JOIN active_users au ON r.user_id = au.user_id
                JOIN popular_movies pm ON r.movie_id = pm.movie_id;
            """)
            alt_filtered = cursor.fetchone()[0]
            print(f"\n   min_user={min_user:2d}, min_movie={min_movie:3d} → {alt_filtered:,} ratings ({(alt_filtered/total_ratings*100):.2f}%)")
        
        print("\n" + "=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données: {e}")
        print("\n💡 Assurez-vous que Docker est lancé et que PostgreSQL est accessible.")

if __name__ == "__main__":
    check_database_stats()

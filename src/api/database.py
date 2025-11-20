import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ta_base_de_donnees")
DB_USER = os.getenv("DB_USER", "ton_utilisateur")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ton_mot_de_passe")

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

def get_db_connection():
    return connection_pool.getconn()

def release_db_connection(conn):
    connection_pool.putconn(conn)

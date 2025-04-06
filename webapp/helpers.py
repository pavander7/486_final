import psycopg2
from .config import Config

def get_db_connection():
    return psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
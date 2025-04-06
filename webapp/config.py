import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")  # change this in production!

    # PostgreSQL settings
    DB_NAME = os.environ.get("DB_NAME", "openFDA")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "yourpassword")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", 5432)

    @classmethod
    def get_db_uri(cls):
        return f"dbname={cls.DB_NAME} user={cls.DB_USER} password={cls.DB_PASSWORD} host={cls.DB_HOST} port={cls.DB_PORT}"

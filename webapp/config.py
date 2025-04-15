import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('POSTGRES_USERNAME')}:{os.environ.get('POSTGRES_PASSWORD')}@" \
        f"{os.environ.get('POSTGRES_HOSTNAME')}:{os.environ.get('POSTGRES_PORT', 5433)}/" \
        f"{os.environ.get('POSTGRES_DBNAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Search settings
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'
    
    # API Keys
    FDA_API_KEY = os.environ.get('FDA_API_KEY')
    DRUGBANK_API_KEY = os.environ.get('DRUGBANK_API_KEY')
    
    # Application settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('FLASK_TESTING', 'False').lower() == 'true'

    # PostgreSQL settings
    DB_NAME = os.environ.get("DB_NAME", "postgres")
    DB_USER = os.environ.get("DB_USER", "thamim")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", 5433)

    @classmethod
    def get_db_uri(cls):
        return f"dbname={cls.DB_NAME} user={cls.DB_USER} password={cls.DB_PASSWORD} host={cls.DB_HOST} port={cls.DB_PORT}"

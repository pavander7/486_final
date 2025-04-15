from webapp import create_app, db
from webapp.models.drug import Drug
from webapp.models.interaction import DrugInteraction
from webapp.services.search import SearchService
from webapp.config import Config
from sqlalchemy import text
import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the data directory to the path so we can import the data loading scripts
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))
from import_all import import_all_data

def init_db():
    """Initialize the database and create tables."""
    # First, create the schema using psycopg2
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DBNAME', 'postgres'),
        user=os.getenv('POSTGRES_USERNAME', 'thamim'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        host=os.getenv('POSTGRES_HOSTNAME', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5433')
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Drop and recreate schema
    cur.execute('DROP SCHEMA IF EXISTS openfda CASCADE')
    cur.execute('CREATE SCHEMA openfda')
    
    # Execute schema.sql
    with open('postgres/schema.sql', 'r') as f:
        cur.execute(f.read())
    
    cur.close()
    conn.close()
    
    # Now initialize the Flask app
    app = create_app()
    
    with app.app_context():
        # Run the postgres data loading pipeline
        print("Loading data from openFDA...")
        subprocess.run(['python', 'postgres/postgres.py', '--verbose'])
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 
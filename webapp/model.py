import psycopg2
from psycopg2 import sql
from flask import current_app

def get_db_connection():
    """Initialize the DB connection."""
    conn = psycopg2.connect(current_app.config['get_db_uri']())
    conn.autocommit = True
    return conn

def get_medications_by_name(prefix):
    """Query medications by name, returning a list of names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = sql.SQL("SELECT name, drugid FROM medications WHERE name ILIKE %s ORDER BY name LIMIT 10")
    cursor.execute(query, (prefix + '%',))
    meds = [{'name': row[0], 'drugid': row[1]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return meds

def get_drugid_by_name(med_name):
    """Get a drugid by name (returns single entry or None)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = sql.SQL("SELECT drugid FROM medications WHERE name = %s LIMIT 1")
    cursor.execute(query, (med_name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def init_db(app):
    """Initialize any DB-level setup or helpers (like a pool or schema check)."""
    # For now, just ensure the database is ready
    # (can add more setup logic here as needed)
    pass  # Placeholder for anything that needs initializing at app startup


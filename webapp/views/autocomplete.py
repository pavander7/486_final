import psycopg2
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname='openFDA',
        user='paulvanderwoude',
        host='localhost',
        port='5432'
    )

@app.route('/autocomplete')
def autocomplete():
    term = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, drugid
        FROM medications
        WHERE name ILIKE %s
        ORDER BY name
        LIMIT 10
    """, (term + '%',))
    results = [{'name': row[0], 'drugid': row[1]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(results)
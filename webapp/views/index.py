from flask import request, jsonify, render_template, current_app
from . import views_bp
from postgres.helpers import get_db_conn
import psycopg2

@views_bp.route('/')
def index():
    # This route serves the main page (index.html) when users visit the home page
    return render_template('index.html')  # Render the index.html template

@views_bp.route('/autocomplete')
def autocomplete():
    term = request.args.get('q', '')

    if not term:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT med_name, drugid, generic_name, brand_name, source
            FROM openfda.medications
            WHERE med_name ILIKE %s
            ORDER BY med_name
            LIMIT 10
        """, (term + '%',))
        
        results = [
            {
                'med_name': row[0],
                'drugid': row[1],
                'generic_names': [v.strip() for v in row[2]],
                'brand_names': [v.strip() for v in row[3]],
                'source': row[4]
            }
            for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()

        if not results:
            return jsonify({"message": "No medications found for your query."}), 404

        return jsonify(results)

    except psycopg2.DatabaseError as e:
        # Log and handle DB errors
        current_app.logger.error(f"Database error: {e}")
        return jsonify({"error": "An error occurred while fetching data. Please try again later."}), 500

    except Exception as e:
        # Log and handle unexpected errors
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

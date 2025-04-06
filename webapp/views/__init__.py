from flask import Blueprint, request, jsonify, current_app
from webapp.model import get_medications_by_name
from psycopg2 import OperationalError

# Create a blueprint for views
views_bp = Blueprint('views', __name__)

# Autocomplete route for returning medication suggestions
@views_bp.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400  # Return error if no query is provided

    try:
        # Fetch medications from the model
        medications = get_medications_by_name(query)

        if not medications:
            return jsonify({"message": "No medications found for your query."}), 404  # Message when no meds are found

        # Return medications in JSON format
        results = [{'name': med['name'], 'drugid': med['drugid']} for med in medications]
        return jsonify(results)
    
    except OperationalError as e:
        # Log the error and return a friendly message
        current_app.logger.error(f"Database error: {e}")
        return jsonify({"error": "An error occurred while fetching data. Please try again later."}), 500
    
    except Exception as e:
        # Log any unexpected error
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

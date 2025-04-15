from flask import Blueprint, render_template, request, jsonify, current_app
from webapp.models.drug import Drug
from webapp.services.search import SearchService
from webapp.services.interaction import InteractionService

main = Blueprint('main', __name__)

def get_search_service():
    return SearchService(current_app.config['ELASTICSEARCH_URL'])

interaction_service = InteractionService()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/search', methods=['POST'])
def search_drugs():
    search_service = get_search_service()
    query = request.json.get('query', '')
    results = search_service.search(query)
    return jsonify(results)

@main.route('/interactions', methods=['POST'])
def check_interactions():
    drug_ids = request.json.get('drugs', [])
    interactions = interaction_service.check_interactions(drug_ids)
    return jsonify(interactions)

@main.route('/drug/<drug_id>')
def get_drug_details(drug_id):
    drug = Drug.query.get_or_404(drug_id)
    return jsonify(drug.to_dict())

@main.route('/accessibility')
def accessibility_settings():
    return render_template('accessibility.html') 
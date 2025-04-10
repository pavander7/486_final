from flask import request, jsonify, render_template, current_app
import psycopg2

from . import views_bp
from postgres.helpers import get_db_connection
from search.search import get_med_info, execute_query

@views_bp.route('/interaction-results')
def serve_results():
    medinfo = {}
    meds = request.args.getlist('meds')

    for med in meds:
        medinfo[med] = get_med_info(med)

    query_results = execute_query(meds)

    context = {'meds': meds, 'medinfo': medinfo, 'query_results': query_results}
    render_template('interaction-results.html', **context)

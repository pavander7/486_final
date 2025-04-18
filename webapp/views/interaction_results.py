from flask import request, render_template

from . import views_bp
from search.search_functions import get_med_info, execute_query

@views_bp.route('/interaction-results')
def serve_results():
    drugnames = request.args.getlist('drugnames')

    # ITEM ONE: druginfo
    druginfo = {}

    for drugname in drugnames:
        label_warning = get_med_info(drugname)
        druginfo[drugname] = label_warning

    # ITEM TWO: events results
    query_results, reaction_summary, strong_results, serious_results = execute_query(drugnames)
    strength = strong_results/len(query_results) * 100
    seriousness = serious_results/len(query_results) * 100

    context = {'druginfo': druginfo, 'reaction_summary': reaction_summary, 'num_reports': len(query_results), 'risk': strength, 'seriousness': seriousness}
    render_template('interaction-results.html', **context)

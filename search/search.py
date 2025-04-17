# search functions
from collections import Counter
from os import abort

from es_search import search_reports
from postgres.helpers import get_db_conn

def get_med_info(drugid):
    """Collects medication information from the DB."""
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT generic_name, drug_interactions
        FROM openfda.drugs
        WHERE drugid = %s
    """, (drugid,))

    info_raw = cursor.fetchone()
    if info_raw is None:
        abort(404)

    drugname = None
    generic_name = info_raw[0]
    if generic_name and isinstance(generic_name, list) and len(generic_name) > 0:
        drugname = generic_name[0]
    else:
        abort(500)
    label_warning = info_raw[1]

    cursor.close()
    conn.close()

    return drugname, label_warning

def get_reactions_and_seriousness(reportid):
    conn = get_db_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT seriousness FROM openfda.reports WHERE reportid = %s
    """, (reportid,))
    serious = cursor.fetchone()[0]

    cursor.execute("""
        SELECT reactionmeddrapt FROM openfda.reactions 
        WHERE reportid = %s AND reactionoutcome <> 6 AND reactionoutcome IS NOT NULL
    """, (reportid,))
    reactions = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return serious, reactions

def execute_query(drugnames):
    """Execute semantic query over ES, enrich with metadata."""
    results = search_reports(drugnames)
    
    for entry in results:
        serious, reactions = get_reactions_and_seriousness(entry["reportid"])
        entry["serious"] = serious
        entry["reactions"] = reactions

    # Aggregate top reaction types
    reaction_counter = Counter()
    for r in results:
        reaction_counter.update(r["reactions"])

    top_reactions = dict(reaction_counter.most_common(10))
    strong_reports = [r for r in results if r["serious"] == 1]

    return results, top_reactions, len(strong_reports), len(strong_reports)
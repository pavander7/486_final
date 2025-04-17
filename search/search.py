from es_search import search_reports
from postgres.auth import Auth

def get_characterizations(reportid):
    """Get drugid + characterization for a report."""
    conn = Auth.get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT drugid, characterization
        FROM openfda.drugreports
        WHERE reportid = %s
    """, (reportid,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return {drugid: char for drugid, char in results}

def get_drugid_name_mapping():
    """Map all drug names to drugids."""
    conn = Auth.get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT drugid, name FROM openfda.medications
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # name is lowercase string, drugid is int or str
    return {name.lower(): str(drugid) for drugid, name in rows}

def get_reactions_and_seriousness(reportid):
    conn = Auth.get_db_conn()
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
    """Execute semantic query over ES, enrich with metadata and drug characterization info."""

    drugnames = [d.lower() for d in drugnames]
    name_to_drugid = get_drugid_name_mapping()
    target_drugids = {name_to_drugid[name] for name in drugnames if name in name_to_drugid}

    results = search_reports(drugnames)
    
    strong_reports = []
    all_reactions = []

    for entry in results:
        reportid = entry["reportid"]
        serious, reactions = get_reactions_and_seriousness(reportid)
        char_map = get_characterizations(reportid)

        in_relevant = {drugid for drugid, char in char_map.items() if drugid in target_drugids and char == 1}
        
        entry["serious"] = serious
        entry["reactions"] = reactions
        entry["char_match"] = len(in_relevant) > 0  # True if any queried drug is a likely cause

        all_reactions.extend(reactions)
        if entry["char_match"]:
            strong_reports.append(entry)

    from collections import Counter
    top_reactions = dict(Counter(all_reactions).most_common(10))

    return results, top_reactions, len(strong_reports), sum(r["serious"] for r in strong_reports)

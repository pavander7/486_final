import psycopg2
import psycopg2.extras

from postgres.auth import Auth

def get_reports(limit=1000):
    conn = Auth.get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # 1. Grab base reports
    cur.execute(f"""
        SELECT report_id, 
               serious, 
               seriousnessdeath, 
               seriousness, 
               seriousnesslifethreatening, 
               seriousnesshospitalization, 
               seriousnessdisabling, 
               seriousnesscongenitalanomali, 
               seriousnessother, 
               patientonsetage, 
               patientsex, 
               patientweight
        FROM openfda.reports
        LIMIT %s
    """, (limit,))

    reports = [dict(row) for row in cur.fetchall()]

    # 2. Build mapping: reportid → reactions
    cur.execute("""
        SELECT reportid, reactionmeddrapt, reactionoutcome
        FROM openfda.reactions
    """)
    reaction_map = {}
    for row in cur.fetchall():
        reportid = row["reportid"]
        reactiontype = row["reactionmeddrapt"]
        reactionoutcome = row["reactionoutcome"]
        match (reactionoutcome):
            case 1:
                reaction = ' '.join([reactiontype, '(recovered)'])
            case 2:
                reaction = ' '.join([reactiontype, '(recovering)'])
            case 3:
                reaction = ' '.join([reactiontype, '(unresolved)'])
            case 4:
                reaction = ' '.join([reactiontype, '(recovered with sequelae)'])
            case 5:
                reaction = ' '.join([reactiontype, '(fatal)'])
            case _:
                reaction = reactiontype
        if reportid not in reaction_map:
            reaction_map[reportid] = []
        reaction_map[reportid].append(reaction)
    
    # 3. Build mapping: reportid → drugs
    cur.execute("""
        SELECT dr.reportid, d.brand_name, d.generic_name
        FROM openfda.drugreports dr
        JOIN openfda.drugs d ON dr.drugid = d.drugid
    """)
    drug_map = {}
    for row in cur.fetchall():
        reportid = row["reportid"]
        drugs = []
        for name_list in (row["brand_name"], row["generic_name"]):
            if name_list:
                drugs.extend(name_list)
        if reportid not in drug_map:
            drug_map[reportid] = []
        drug_map[reportid].extend(d for d in drugs if d)

    cur.close()
    conn.close()

    # 4. Enrich reports with drug + reaction info
    for report in reports:
        rid = report["reportid"]
        report["drugnames"] = drug_map.get(rid, [])
        report["reactions"] = reaction_map.get(rid, [])

    return reports

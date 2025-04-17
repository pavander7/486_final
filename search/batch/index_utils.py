from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import psycopg2
import psycopg2.extras

from postgres.auth import Auth

es = Elasticsearch("http://localhost:9200")

index_name = "reports_embeddings"

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

mapping = {
    "mappings": {
        "properties": {
            "reportid": {"type": "keyword"},
            "text": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

def check_init():
    """Check if the ElasticSearch index is initialized."""
    return es.indices.exists(index=index_name)

def init_es():
    """Initialize ElasticSearch index."""
    # Delete the index if it already exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    # Create the index
    es.indices.create(index=index_name, body=mapping)

print(f"Created Elasticsearch index '{index_name}' for adverse event reports.")

def embed_text(text):
    """Embed text using SentenceTransformer."""
    return model.encode(text).tolist()

def index_to_elasticsearch(report_id, synthetic_text, embedding):
    """Add report to ElasticSearch index."""
    doc = {
        "reportid": report_id,
        "text": synthetic_text,
        "embedding": embedding
    }
    es.index(index=index_name, id=report_id, body=doc)

def get_reports(limit=1000):
    """Retrieve batch of results from postgres."""
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
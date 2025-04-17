from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

from postgres.auth import Auth

es = Elasticsearch("http://localhost:9200")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def search_reports(drugnames, top_k=20):
    query_text = f"Reports involving: {', '.join(drugnames)}"
    embedding = model.encode(query_text).tolist()

    query_body = {
        "size": top_k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": embedding}
                }
            }
        }
    }

    results = es.search(index="reports_embeddings", body=query_body)

    # Parse out results
    parsed = []
    for hit in results["hits"]["hits"]:
        source = hit["_source"]
        parsed.append({
            "reportid": source["reportid"],
            "text": source["synthetic_text"],
            "score": hit["_score"]
        })

    return parsed

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
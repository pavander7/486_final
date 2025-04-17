# es_search.py

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from text_utils import create_synthetic_text
from db_utils import get_reports  # if you want to enrich results
import numpy as np

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

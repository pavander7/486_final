from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

es = Elasticsearch("http://localhost:9200")

index_name = "reports_embeddings"

mapping = {
    "mappings": {
        "properties": {
            "reportid": {"type": "keyword"},
            "text": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": 384,  # Adjust this to match your model's embedding size
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

def init_es():
    # Delete the index if it already exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    # Create the index
    es.indices.create(index=index_name, body=mapping)

print(f"Created Elasticsearch index '{index_name}' for adverse event reports.")

def index_to_elasticsearch(report_id, synthetic_text, embedding):
    doc = {
        "reportid": report_id,
        "text": synthetic_text,
        "embedding": embedding
    }
    es.index(index=index_name, id=report_id, body=doc)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_text(text):
    return model.encode(text).tolist()
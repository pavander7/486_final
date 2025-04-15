from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from typing import List, Dict, Any
from flask import current_app
from webapp.models.drug import Drug
import ssl
import certifi
import os

class SearchService:
    def __init__(self, es_url=None):
        """Initialize the search service with Elasticsearch connection."""
        if es_url is None:
            es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        
        # Create Elasticsearch client with basic auth
        self.es = Elasticsearch(es_url)
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.model = AutoModel.from_pretrained('bert-base-uncased')
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create the Elasticsearch index if it doesn't exist."""
        if not self.es.indices.exists(index='drugs'):
            self.es.indices.create(
                index='drugs',
                body={
                    'mappings': {
                        'properties': {
                            'brand_name': {'type': 'text'},
                            'generic_name': {'type': 'text'},
                            'substance_name': {'type': 'text'},
                            'description': {'type': 'text'},
                            'embedding': {'type': 'dense_vector', 'dims': 768}
                        }
                    }
                }
            )
    
    def _get_bert_embedding(self, text: str) -> np.ndarray:
        """Get BERT embedding for a text string."""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()[0]
    
    def index_drug(self, drug: Drug):
        """Index a drug in Elasticsearch with its BERT embedding."""
        doc = {
            'brand_name': drug.brand_name,
            'generic_name': drug.generic_name,
            'substance_name': drug.substance_name,
            'description': f"{drug.brand_name} {drug.generic_name} {drug.substance_name}",
            'embedding': self._get_bert_embedding(f"{drug.brand_name} {drug.generic_name} {drug.substance_name}")
        }
        self.es.index(index='drugs', id=drug.drugid, document=doc)
    
    def search(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs using hybrid search (lexical + semantic)."""
        # Get BERT embedding for the query
        query_embedding = self._get_bert_embedding(query)
        
        # Perform hybrid search
        response = self.es.search(
            index='drugs',
            body={
                'query': {
                    'bool': {
                        'should': [
                            # Lexical search
                            {
                                'multi_match': {
                                    'query': query,
                                    'fields': ['brand_name^3', 'generic_name^2', 'substance_name'],
                                    'type': 'best_fields'
                                }
                            },
                            # Semantic search
                            {
                                'script_score': {
                                    'query': {'match_all': {}},
                                    'script': {
                                        'source': 'cosineSimilarity(params.query_vector, "embedding") + 1.0',
                                        'params': {'query_vector': query_embedding.tolist()}
                                    }
                                }
                            }
                        ]
                    }
                },
                'size': size
            }
        )
        
        # Process and return results
        results = []
        for hit in response['hits']['hits']:
            drug = Drug.query.get(hit['_id'])
            if drug:
                results.append({
                    'drugid': drug.drugid,
                    'name': drug.brand_name or drug.generic_name,
                    'description': f"{drug.generic_name} ({drug.brand_name})" if drug.brand_name else drug.generic_name,
                    'score': hit['_score']
                })
        
        return results
    
    def reindex_all_drugs(self):
        """Reindex all drugs in the database."""
        drugs = Drug.query.all()
        for drug in drugs:
            self.index_drug(drug)
    
    def delete_index(self):
        """Delete the Elasticsearch index."""
        if self.es.indices.exists(index='drugs'):
            self.es.indices.delete(index='drugs') 
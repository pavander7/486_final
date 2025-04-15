from flask import Flask, render_template
from webapp import create_app
from webapp.services.search import SearchService
from webapp.services.interaction import InteractionService
from webapp.models.drug import Drug
from webapp.models.interaction import DrugInteraction
from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
from sqlalchemy import func, text
import re
from webapp import db
import json

# Load environment variables
load_dotenv()

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

def extract_interactions_from_labels():
    """Extract interactions from drug labels and store them in the interactions table."""
    # Get all drugs with interaction information
    drugs = db.session.query(Drug).filter(text("drug_interactions IS NOT NULL")).all()
    total_drugs = len(drugs)
    print(f"\nStarting interaction extraction for {total_drugs} drugs...")
    
    for idx, drug in enumerate(drugs, 1):
        if not drug.drug_interactions:
            continue
            
        # Print progress every 10 drugs
        if idx % 10 == 0:
            print(f"Processing drug {idx}/{total_drugs}...")
            
        try:
            # Try to parse the interaction text as JSON
            interaction_data = json.loads(drug.drug_interactions)
            if not isinstance(interaction_data, dict):
                continue
                
            # Extract drug names from the interaction text
            interaction_text = str(interaction_data).lower()
            
            # Get current drug's names (normalized)
            current_drug_names = []
            if drug.brand_name:
                current_drug_names.extend([name.lower().strip() for name in drug.brand_name])
            if drug.generic_name:
                current_drug_names.extend([name.lower().strip() for name in drug.generic_name])
            
            # Look for other drugs mentioned in the interaction text
            for other_drug in Drug.query.all():
                if other_drug.drugid == drug.drugid:
                    continue
                    
                # Get other drug's names (normalized)
                other_drug_names = []
                if other_drug.brand_name:
                    other_drug_names.extend([name.lower().strip() for name in other_drug.brand_name])
                if other_drug.generic_name:
                    other_drug_names.extend([name.lower().strip() for name in other_drug.generic_name])
                
                # Check for direct interaction by looking for both drugs mentioned together
                for current_name in current_drug_names:
                    for other_name in other_drug_names:
                        if not current_name or not other_name:
                            continue
                            
                        # Create patterns to look for
                        patterns = [
                            f"{current_name} and {other_name}",  # "atenolol and chlorthalidone"
                            f"{other_name} and {current_name}",  # "chlorthalidone and atenolol"
                            f"{current_name} with {other_name}",  # "atenolol with chlorthalidone"
                            f"{other_name} with {current_name}",  # "chlorthalidone with atenolol"
                            f"{current_name}/{other_name}",      # "atenolol/chlorthalidone"
                            f"{other_name}/{current_name}"       # "chlorthalidone/atenolol"
                        ]
                        
                        # Check if any pattern is found in the interaction text
                        for pattern in patterns:
                            if pattern in interaction_text:
                                # Found a direct interaction
                                interaction = DrugInteraction(
                                    drug1_id=min(drug.drugid, other_drug.drugid),
                                    drug2_id=max(drug.drugid, other_drug.drugid),
                                    severity='medium',  # Default severity
                                    description=f"Interaction between {current_name} and {other_name}: {interaction_text[:200]}...",
                                    source="Drug Label",
                                    evidence_level="moderate"
                                )
                                
                                # Check if this interaction already exists
                                existing = DrugInteraction.query.filter_by(
                                    drug1_id=interaction.drug1_id,
                                    drug2_id=interaction.drug2_id
                                ).first()
                                
                                if not existing:
                                    db.session.add(interaction)
                                    print(f"Found interaction: {current_name} and {other_name}")
                                break  # Found a match, no need to check other patterns
        except json.JSONDecodeError:
            # If it's not JSON, treat it as plain text
            interaction_text = drug.drug_interactions.lower()
            
            # Get current drug's names (normalized)
            current_drug_names = []
            if drug.brand_name:
                current_drug_names.extend([name.lower().strip() for name in drug.brand_name])
            if drug.generic_name:
                current_drug_names.extend([name.lower().strip() for name in drug.generic_name])
            
            # Look for other drugs mentioned in the interaction text
            for other_drug in Drug.query.all():
                if other_drug.drugid == drug.drugid:
                    continue
                    
                # Get other drug's names (normalized)
                other_drug_names = []
                if other_drug.brand_name:
                    other_drug_names.extend([name.lower().strip() for name in other_drug.brand_name])
                if other_drug.generic_name:
                    other_drug_names.extend([name.lower().strip() for name in other_drug.generic_name])
                
                # Check for direct interaction by looking for both drugs mentioned together
                for current_name in current_drug_names:
                    for other_name in other_drug_names:
                        if not current_name or not other_name:
                            continue
                            
                        # Create patterns to look for
                        patterns = [
                            f"{current_name} and {other_name}",
                            f"{other_name} and {current_name}",
                            f"{current_name} with {other_name}",
                            f"{other_name} with {current_name}",
                            f"{current_name}/{other_name}",
                            f"{other_name}/{current_name}"
                        ]
                        
                        # Check if any pattern is found in the interaction text
                        for pattern in patterns:
                            if pattern in interaction_text:
                                # Found a direct interaction
                                interaction = DrugInteraction(
                                    drug1_id=min(drug.drugid, other_drug.drugid),
                                    drug2_id=max(drug.drugid, other_drug.drugid),
                                    severity='medium',  # Default severity
                                    description=f"Interaction between {current_name} and {other_name}: {interaction_text[:200]}...",
                                    source="Drug Label",
                                    evidence_level="moderate"
                                )
                                
                                # Check if this interaction already exists
                                existing = DrugInteraction.query.filter_by(
                                    drug1_id=interaction.drug1_id,
                                    drug2_id=interaction.drug2_id
                                ).first()
                                
                                if not existing:
                                    db.session.add(interaction)
                                    print(f"Found interaction: {current_name} and {other_name}")
                                break  # Found a match, no need to check other patterns
    
    db.session.commit()
    print("\nInteraction extraction complete!")

if __name__ == '__main__':
    with app.app_context():
        # Initialize search service
        search_service = SearchService()
        
        # Check if drugs index exists and has documents
        es = Elasticsearch(os.getenv('ELASTICSEARCH_URL'))
        if not es.indices.exists(index='drugs') or es.count(index='drugs')['count'] == 0:
            print("Drugs index is empty or doesn't exist. Reindexing all drugs in Elasticsearch...")
            search_service.reindex_all_drugs()
            print("Reindexing complete!")
        else:
            print("Drugs index already exists with data. Skipping reindexing.")
        
        # Check if we have any interactions in the database
        interaction_count = DrugInteraction.query.count()
        if interaction_count == 0:
            print("No interactions found in database. Extracting interactions from drug labels...")
            extract_interactions_from_labels()
            print("Interaction extraction complete!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)

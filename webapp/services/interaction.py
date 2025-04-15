from typing import List, Dict, Any
from webapp.models.drug import Drug
from webapp.models.interaction import DrugInteraction
from webapp import db

class InteractionService:
    def check_interactions(self, drug_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Check for interactions between the given drugs.
        
        Args:
            drug_ids: List of drug IDs to check interactions for
            
        Returns:
            List of interaction dictionaries
        """
        if len(drug_ids) < 2:
            return []
        
        # Get all possible pairs of drugs
        drug_pairs = []
        for i in range(len(drug_ids)):
            for j in range(i + 1, len(drug_ids)):
                drug_pairs.append((drug_ids[i], drug_ids[j]))
        
        # Query for interactions
        interactions = []
        for drug1_id, drug2_id in drug_pairs:
            # Ensure drug1_id is less than drug2_id to match our constraint
            if drug1_id > drug2_id:
                drug1_id, drug2_id = drug2_id, drug1_id
            
            interaction = DrugInteraction.query.filter_by(
                drug1_id=drug1_id,
                drug2_id=drug2_id
            ).first()
            
            if interaction:
                interactions.append(interaction.to_dict())
        
        return interactions
    
    def add_interaction(self, drug1_id: int, drug2_id: int, 
                       severity: str, description: str,
                       mechanism: str = None, recommendation: str = None,
                       evidence_level: str = None, source: str = None,
                       source_url: str = None) -> DrugInteraction:
        """
        Add a new drug interaction to the database.
        
        Args:
            drug1_id: ID of the first drug
            drug2_id: ID of the second drug
            severity: Severity level ('high', 'medium', 'low')
            description: Description of the interaction
            mechanism: Mechanism of interaction (optional)
            recommendation: Recommendation for handling the interaction (optional)
            evidence_level: Level of evidence ('strong', 'moderate', 'weak') (optional)
            source: Source of the interaction information (optional)
            source_url: URL to the source (optional)
            
        Returns:
            The created DrugInteraction object
        """
        # Ensure drug1_id is less than drug2_id
        if drug1_id > drug2_id:
            drug1_id, drug2_id = drug2_id, drug1_id
        
        # Check if interaction already exists
        existing = DrugInteraction.query.filter_by(
            drug1_id=drug1_id,
            drug2_id=drug2_id
        ).first()
        
        if existing:
            # Update existing interaction
            existing.severity = severity
            existing.description = description
            existing.mechanism = mechanism
            existing.recommendation = recommendation
            existing.evidence_level = evidence_level
            existing.source = source
            existing.source_url = source_url
            db.session.commit()
            return existing
        
        # Create new interaction
        interaction = DrugInteraction(
            drug1_id=drug1_id,
            drug2_id=drug2_id,
            severity=severity,
            description=description,
            mechanism=mechanism,
            recommendation=recommendation,
            evidence_level=evidence_level,
            source=source,
            source_url=source_url
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        return interaction
    
    def delete_interaction(self, drug1_id: int, drug2_id: int) -> bool:
        """
        Delete a drug interaction from the database.
        
        Args:
            drug1_id: ID of the first drug
            drug2_id: ID of the second drug
            
        Returns:
            True if interaction was deleted, False if not found
        """
        # Ensure drug1_id is less than drug2_id
        if drug1_id > drug2_id:
            drug1_id, drug2_id = drug2_id, drug1_id
        
        interaction = DrugInteraction.query.filter_by(
            drug1_id=drug1_id,
            drug2_id=drug2_id
        ).first()
        
        if interaction:
            db.session.delete(interaction)
            db.session.commit()
            return True
        
        return False 
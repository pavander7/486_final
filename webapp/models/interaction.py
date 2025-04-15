from datetime import datetime
from webapp import db

class DrugInteraction(db.Model):
    __tablename__ = 'drug_interactions'
    __table_args__ = {'schema': 'openfda'}
    
    id = db.Column(db.Integer, primary_key=True)
    drug1_id = db.Column(db.String(100), db.ForeignKey('openfda.drugs.drugid'), nullable=False)
    drug2_id = db.Column(db.String(100), db.ForeignKey('openfda.drugs.drugid'), nullable=False)
    severity = db.Column(db.String(50), nullable=False)  # 'high', 'medium', 'low'
    description = db.Column(db.Text, nullable=False)
    mechanism = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    evidence_level = db.Column(db.String(50))  # 'strong', 'moderate', 'weak'
    source = db.Column(db.String(200))
    source_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure drug1_id is always less than drug2_id to prevent duplicate interactions
    __table_args__ = (
        db.CheckConstraint('drug1_id < drug2_id', name='check_drug_order'),
        {'schema': 'openfda'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug1': self.drug1.to_dict(),
            'drug2': self.drug2.to_dict(),
            'severity': self.severity,
            'description': self.description,
            'mechanism': self.mechanism,
            'recommendation': self.recommendation,
            'evidence_level': self.evidence_level,
            'source': self.source,
            'source_url': self.source_url
        }
    
    def __repr__(self):
        return f'<Interaction between {self.drug1.brand_name} and {self.drug2.brand_name}>' 
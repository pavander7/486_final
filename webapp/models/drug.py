from datetime import datetime
from webapp import db
from sqlalchemy.dialects.postgresql import ARRAY

class Drug(db.Model):
    __tablename__ = 'drugs'
    __table_args__ = {'schema': 'openfda'}
    
    drugid = db.Column(db.String(100), primary_key=True)
    brand_name = db.Column(ARRAY(db.String(200)))
    generic_name = db.Column(ARRAY(db.String(200)))
    manufacturer_name = db.Column(db.String(200))
    product_ndc = db.Column(db.String(50))
    product_type = db.Column(db.String(100))
    administration_route = db.Column(db.String(100))
    substance_name = db.Column(db.String(200))
    rxcui = db.Column(db.String(50))
    spl_id = db.Column(db.String(100))
    spl_set_id = db.Column(db.String(100))
    package_ndc = db.Column(db.String(50))
    nui = db.Column(db.String(50))
    pharm_class_epc = db.Column(db.String(200))
    pharm_class_moa = db.Column(db.String(200))
    unii = db.Column(db.String(50))
    drug_interactions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = db.relationship('DrugInteraction', 
                                 foreign_keys='DrugInteraction.drug1_id',
                                 backref='drug1',
                                 lazy='dynamic')
    interactions_with = db.relationship('DrugInteraction',
                                      foreign_keys='DrugInteraction.drug2_id',
                                      backref='drug2',
                                      lazy='dynamic')
    
    def to_dict(self):
        return {
            'drugid': self.drugid,
            'brand_name': self.brand_name[0] if self.brand_name else None,
            'generic_name': self.generic_name[0] if self.generic_name else None,
            'manufacturer_name': self.manufacturer_name,
            'product_ndc': self.product_ndc,
            'product_type': self.product_type,
            'administration_route': self.administration_route,
            'substance_name': self.substance_name,
            'rxcui': self.rxcui,
            'spl_id': self.spl_id,
            'spl_set_id': self.spl_set_id,
            'package_ndc': self.package_ndc,
            'nui': self.nui,
            'pharm_class_epc': self.pharm_class_epc,
            'pharm_class_moa': self.pharm_class_moa,
            'unii': self.unii,
            'drug_interactions': self.drug_interactions
        }
    
    def __repr__(self):
        brand = self.brand_name[0] if self.brand_name else 'Unknown'
        generic = self.generic_name[0] if self.generic_name else 'Unknown'
        return f'<Drug {brand} ({generic})>' 
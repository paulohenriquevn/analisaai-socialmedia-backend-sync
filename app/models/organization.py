"""
Organization-related models.
"""
from datetime import datetime
from app.extensions import db
# Import user_organization association table from User model
# We need to reference it but can't import it directly to avoid circular imports

class Organization(db.Model):
    """Organization model for grouping users and managed socialpage."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    
    # Relationships
    plan = db.relationship('Plan', backref='organizations')
    
    def __repr__(self):
        return f'<Organization {self.name}>'


class Plan(db.Model):
    """Subscription plan model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    
    # Relationships
    features = db.relationship('PlanFeature', backref='plan')
    
    def __repr__(self):
        return f'<Plan {self.name}>'


class PlanFeature(db.Model):
    """Features included in a subscription plan."""
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    feature = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<PlanFeature {self.feature}>'
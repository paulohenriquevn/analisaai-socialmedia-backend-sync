"""
User-related models.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

# Association table for User-Role relationship
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Association table for Organization-User relationship
organization_users = db.Table('organization_users',
    db.Column('organization_id', db.Integer, db.ForeignKey('organization.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(db.Model):
    """User model representing system users.
    
    OBS: Para maior extensibilidade, considere migrar os campos de redes sociais (facebook_id, instagram_id, etc.) para uma tabela relacional UserSocialAccount no futuro.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Social media IDs
    facebook_id = db.Column(db.String(100), unique=True, nullable=True)
    instagram_id = db.Column(db.String(100), unique=True, nullable=True)
    tiktok_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Social media usernames
    facebook_username = db.Column(db.String(100), nullable=True)
    instagram_username = db.Column(db.String(100), nullable=True)
    tiktok_username = db.Column(db.String(100), nullable=True)
    
    # Profile information
    profile_image = db.Column(db.String(500), nullable=True)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    social_tokens = db.relationship('SocialToken', backref='user', lazy='dynamic')
    organizations = db.relationship('Organization', secondary=organization_users, backref=db.backref('users', lazy='dynamic'))
    social_pages = db.relationship('SocialPage', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set the password hash from a plaintext password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has a given role by name."""
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        return f'<User {self.username}>'


class Role(db.Model):
    """Role model for user permissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Role {self.name}>'
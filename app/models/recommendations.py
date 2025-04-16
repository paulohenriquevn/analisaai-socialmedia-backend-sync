from datetime import datetime
from app.extensions import db

class CalendarPost(db.Model):
    __tablename__ = 'calendar_post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    platform = db.Column(db.String(20), nullable=False)
    content_title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, draft, posted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OptimizationTip(db.Model):
    __tablename__ = 'optimization_tip'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    impact = db.Column(db.String(20))  # high/medium/low
    best_practices = db.Column(db.Text)  # Ex: 'prática1;prática2'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trend(db.Model):
    __tablename__ = 'trend'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    popularity = db.Column(db.Integer)
    platforms = db.Column(db.String(255))  # Ex: 'instagram,facebook'
    hashtags = db.Column(db.String(255))   # Ex: '#hashtag1,#hashtag2'
    related_topics = db.Column(db.String(255))  # Ex: 'topico1,topico2'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContentIdea(db.Model):
    __tablename__ = 'content_idea'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    platforms = db.Column(db.String(255))  # Ex: 'instagram,facebook'
    content_type = db.Column(db.String(50))
    tags = db.Column(db.String(255))  # Ex: 'engajamento,dicas'
    estimated_engagement = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedContentIdea(db.Model):
    __tablename__ = 'saved_content_idea'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('content_idea.id', ondelete='CASCADE'), index=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'idea_id', name='uix_user_idea'),)

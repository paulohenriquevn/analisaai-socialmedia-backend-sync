"""
Models related to social media integrations.
"""
from datetime import datetime
from app.extensions import db
from sqlalchemy.schema import Index, UniqueConstraint

social_page_categories = db.Table('social_page_categories',
    db.Column('social_page_id', db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), primary_key=True),
    db.Column('social_page_category_id', db.Integer, db.ForeignKey('social_page_category.id', ondelete='CASCADE'), primary_key=True)
)


class SocialToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    platform = db.Column(db.String(20), nullable=False, index=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text)
    expires_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'platform', name='uix_social_token_user_platform'),
    )
    
    def __repr__(self):
        return f'<SocialToken {self.platform} for user {self.user_id}>'
    
    @property
    def is_expired(self):
        """Check if the token is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class SocialPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    full_name = db.Column(db.String(100))
    platform = db.Column(db.String(20), nullable=False, index=True)
    profile_url = db.Column(db.String(1024))
    profile_image = db.Column(db.Text)
    bio = db.Column(db.Text)
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)
    social_score = db.Column(db.Float, default=0.0)
    relevance_score = db.Column(db.Float, default=0.0)  # Current relevance score (0-100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    categories = db.relationship('SocialPageCategory', secondary=social_page_categories, 
                                backref=db.backref('pages', lazy='dynamic'),
                                cascade="all, delete")
    metrics = db.relationship('SocialPageMetric', backref='social_page', lazy='dynamic',
                             cascade="all, delete-orphan")
    engagements = db.relationship('SocialPageEngagement', backref='social_page', lazy='dynamic',
                                 cascade="all, delete-orphan")
    growths = db.relationship('SocialPageGrowth', backref='social_page', lazy='dynamic',
                             cascade="all, delete-orphan")
    reachs = db.relationship('SocialPageReach', backref='social_page', lazy='dynamic',
                            cascade="all, delete-orphan")
    scores = db.relationship('SocialPageScore', backref='social_page', lazy='dynamic',
                            cascade="all, delete-orphan")
    posts = db.relationship('SocialPagePost', backref='social_page', lazy='dynamic',
                           cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('username', 'platform', name='uix_social_page_username_platform'),
    )
    
    def __repr__(self):
        return f'<SocialPage {self.username} ({self.platform})>'


class SocialPageMetric(db.Model):
    """Model for storing historical metrics about social pages."""
    id = db.Column(db.Integer, primary_key=True)
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    followers = db.Column(db.Integer)
    engagement = db.Column(db.Float)
    posts = db.Column(db.Integer)
    likes = db.Column(db.Integer)
    comments = db.Column(db.Integer)
    shares = db.Column(db.Integer)
    views = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('social_page_id', 'date', name='uix_social_page_metric_page_date'),
    )
    
    def __repr__(self):
        return f'<SocialPageMetric {self.social_page_id} {self.date}>'


class SocialPageEngagement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    posts_count = db.Column(db.Integer, default=0)
    avg_likes_per_post = db.Column(db.Float, default=0.0)
    avg_comments_per_post = db.Column(db.Float, default=0.0)
    avg_shares_per_post = db.Column(db.Float, default=0.0)
    engagement_rate = db.Column(db.Float, default=0.0)
    total_likes = db.Column(db.Integer, default=0)
    total_comments = db.Column(db.Integer, default=0)
    total_shares = db.Column(db.Integer, default=0)
    growth_rate = db.Column(db.Float, default=0.0)  # Growth rate compared to previous period
    video_views = db.Column(db.Integer, default=0)
    reach = db.Column(db.Integer, default=0)
    impressions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('social_page_id', 'date', name='uix_social_page_engagement_page_date'),
    )
    
    def __repr__(self):
        return f'<SocialPageEngagement {self.social_page_id} on {self.date}>'


class SocialPageGrowth(db.Model):
    """Model for tracking growth metrics and growth goals (metas de crescimento)."""
    id = db.Column(db.Integer, primary_key=True)
    # --- Para metas de crescimento (Growth Goals) ---
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True, nullable=True)  # Meta pode ser por usuário
    platform = db.Column(db.String(20), nullable=True, index=True)  # Plataforma da meta (ex: instagram)
    followers_goal = db.Column(db.Integer, nullable=True)  # Meta de seguidores
    engagement_goal = db.Column(db.Float, nullable=True)   # Meta de engajamento
    deadline = db.Column(db.Date, nullable=True)           # Prazo da meta
    is_goal = db.Column(db.Boolean, default=False, index=True)  # True: registro de meta, False: histórico
    # --- Para histórico de crescimento ---
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True, nullable=True)
    date = db.Column(db.Date, nullable=True, index=True)
    followers_count = db.Column(db.Integer, default=0)  # Total followers on this date
    new_followers_daily = db.Column(db.Integer, default=0)  # New followers in the last day
    new_followers_weekly = db.Column(db.Integer, default=0)  # New followers in the last week
    new_followers_monthly = db.Column(db.Integer, default=0)  # New followers in the last month
    retention_rate = db.Column(db.Float, default=0.0)  # Percentage of followers retained (100 - unfollow_rate)
    churn_rate = db.Column(db.Float, default=0.0)  # Percentage of followers lost (unfollow rate)
    daily_growth_rate = db.Column(db.Float, default=0.0)  # Daily growth rate as percentage
    weekly_growth_rate = db.Column(db.Float, default=0.0)  # Weekly growth rate as percentage
    monthly_growth_rate = db.Column(db.Float, default=0.0)  # Monthly growth rate as percentage
    growth_velocity = db.Column(db.Float, default=0.0)  # Average new followers per day over a period
    growth_acceleration = db.Column(db.Float, default=0.0)  # Change in growth velocity
    projected_followers_30d = db.Column(db.Integer, default=0)  # Projected followers count in 30 days
    projected_followers_90d = db.Column(db.Integer, default=0)  # Projected followers count in 90 days
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('social_page_id', 'date', name='uix_social_page_growth_page_date'),
    )
    
    def __repr__(self):
        return f'<SocialPageGrowth goal={self.is_goal} user={self.user_id} page={self.social_page_id}>'


class SocialPageReach(db.Model):
    """Model for tracking reach metrics such as impressions and story views."""
    id = db.Column(db.Integer, primary_key=True)
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    impressions = db.Column(db.Integer, default=0)  # Number of times content was displayed
    reach = db.Column(db.Integer, default=0)  # Number of unique accounts that saw the content
    story_views = db.Column(db.Integer, default=0)  # Number of views on stories
    profile_views = db.Column(db.Integer, default=0)  # Number of profile visits
    stories_count = db.Column(db.Integer, default=0)  # Number of stories posted
    story_engagement_rate = db.Column(db.Float, default=0.0)  # Engagement rate on stories
    story_exit_rate = db.Column(db.Float, default=0.0)  # Rate at which users exit stories
    story_completion_rate = db.Column(db.Float, default=0.0)  # Percentage of users who view stories to completion
    avg_watch_time = db.Column(db.Float, default=0.0)  # Average watch time in seconds (for video content)
    audience_growth = db.Column(db.Float, default=0.0)  # Growth rate of audience since last measurement
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('social_page_id', 'date', name='uix_social_page_reach_page_date'),
    )
    
    def __repr__(self):
        return f'<SocialPageReach {self.social_page_id} on {self.date}>'    


class SocialPageScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    overall_score = db.Column(db.Float, default=0.0)
    engagement_score = db.Column(db.Float, default=0.0)  # Based on engagement metrics
    reach_score = db.Column(db.Float, default=0.0)  # Based on reach metrics
    growth_score = db.Column(db.Float, default=0.0)  # Based on growth metrics
    consistency_score = db.Column(db.Float, default=0.0)  # Based on posting consistency
    audience_quality_score = db.Column(db.Float, default=0.0)  # Based on audience quality
    engagement_weight = db.Column(db.Float, default=0.3)
    reach_weight = db.Column(db.Float, default=0.25)
    growth_weight = db.Column(db.Float, default=0.25)
    consistency_weight = db.Column(db.Float, default=0.1)
    audience_quality_weight = db.Column(db.Float, default=0.1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('social_page_id', 'date', name='uix_social_page_score_page_date'),
    )
    
    def __repr__(self):
        return f'<SocialPageScore {self.social_page_id} on {self.date}: {self.overall_score}>'


class SocialPagePost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False, index=True)
    post_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    social_page_id = db.Column(db.Integer, db.ForeignKey('social_page.id', ondelete='CASCADE'), index=True)
    content = db.Column(db.Text)
    post_url = db.Column(db.Text)
    media_url = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, index=True)
    content_type = db.Column(db.String(20), index=True)  # 'image', 'video', 'carousel', 'text', etc.
    category = db.Column(db.String(50), index=True)  # 'product', 'lifestyle', 'education', etc.
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)  # Calculated engagement rate
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('SocialPagePostComment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SocialPagePost {self.platform}:{self.post_id}>'
        
    @property
    def day_of_week(self):
        """Get the day of week when the post was published."""
        if self.posted_at:
            return self.posted_at.strftime('%A')  # Monday, Tuesday, etc.
        return None
        
    @property
    def hour_of_day(self):
        """Get the hour of day when the post was published."""
        if self.posted_at:
            return self.posted_at.hour
        return None
        
    @property
    def engagement(self):
        """Calculate engagement (sum of likes, comments, shares)."""
        return (self.likes_count or 0) + (self.comments_count or 0) + (self.shares_count or 0)


class SocialPagePostComment(db.Model):
    """Model for storing comments on social media posts."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('social_page_post.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = db.Column(db.String(20), nullable=False, index=True)
    comment_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    author_username = db.Column(db.String(100), index=True)
    author_display_name = db.Column(db.String(100))
    author_picture = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, index=True)
    likes_count = db.Column(db.Integer, default=0)
    replied_to_id = db.Column(db.String(100), index=True)  # ID of parent comment if this is a reply
    
    # Sentiment analysis data
    sentiment = db.Column(db.String(10), index=True)  # positive, neutral, negative
    sentiment_score = db.Column(db.Float)  # -1.0 to 1.0
    is_critical = db.Column(db.Boolean, default=False, index=True)  # Flag for critical comments
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SocialPagePostComment {self.platform}:{self.comment_id}>'
    

class SocialPageCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<SocialPageCategory {self.name}>'

# Create indexes for common queries
Index('idx_social_token_user_platform', SocialToken.user_id, SocialToken.platform)
Index('idx_social_page_user_platform', SocialPage.user_id, SocialPage.platform)
Index('idx_social_page_metrics_date', SocialPageMetric.social_page_id, SocialPageMetric.date)
Index('idx_social_page_post_page_date', SocialPagePost.social_page_id, SocialPagePost.posted_at)

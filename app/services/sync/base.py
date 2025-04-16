from typing import Dict, List, Optional, Any
from datetime import datetime, date
import structlog
from sqlalchemy.orm import Session
from app.models.social_media import (
    SocialPage, SocialToken, SocialPageMetric, SocialPageEngagement,
    SocialPageGrowth, SocialPageReach, SocialPageScore, SocialPagePost,
    SocialPagePostComment
)
from app.models.user import User
from app.worker import celery
from app.utils.encryption import decrypt_value
from app.utils.errors import SocialTokenError, NotFoundError
from app.services.apify_service import ApifyService

# Set up logger
logger = structlog.get_logger("analisaai-sync")

class BaseSyncService:
    """Base class for social media sync services"""
    
    def __init__(self, db: Session):
        """
        Initialize sync service
        
        Args:
            db (Session): Database session
        """
        self.db = db
        self.apify_service = ApifyService()
    
    def get_user(self, user_id: int) -> User:
        """
        Get user by ID
        
        Args:
            user_id (int): User ID
        
        Returns:
            User: User object
        
        Raises:
            NotFoundError: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user
    
    def get_social_token(self, user_id: int, platform: str) -> SocialToken:
        """
        Get social token by user ID and platform
        
        Args:
            user_id (int): User ID
            platform (str): Social media platform (instagram, facebook, tiktok)
        
        Returns:
            SocialToken: Social token object
        
        Raises:
            SocialTokenError: If token not found or expired
        """
        token = (
            self.db.query(SocialToken)
            .filter(SocialToken.user_id == user_id, SocialToken.platform == platform)
            .first()
        )
        
        if not token:
            raise SocialTokenError(f"No {platform} token found for user {user_id}")
        
        if token.is_expired:
            raise SocialTokenError(f"{platform} token for user {user_id} is expired")
        
        return token
    
    def get_social_page(self, user_id: int, platform: str) -> Optional[SocialPage]:
        """
        Get social page by user ID and platform
        
        Args:
            user_id (int): User ID
            platform (str): Social media platform (instagram, facebook, tiktok)
        
        Returns:
            Optional[SocialPage]: Social page object or None if not found
        """
        return (
            self.db.query(SocialPage)
            .filter(SocialPage.user_id == user_id, SocialPage.platform == platform)
            .first()
        )
    
    def create_or_update_social_page(
        self, user_id: int, platform: str, data: Dict
    ) -> SocialPage:
        """
        Create or update social page
        
        Args:
            user_id (int): User ID
            platform (str): Social media platform (instagram, facebook, tiktok)
            data (Dict): Social page data
        
        Returns:
            SocialPage: Created or updated social page
        """
        # Find existing page
        page = self.get_social_page(user_id, platform)
        
        # If page exists, update it
        if page:
            # Update page attributes
            for key, value in data.items():
                if hasattr(page, key):
                    setattr(page, key, value)
            
            # Mark as updated
            page.updated_at = datetime.utcnow()
            
        # Otherwise, create new page
        else:
            # Create page object
            page = SocialPage(
                user_id=user_id,
                platform=platform,
                **data
            )
            self.db.add(page)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(page)
        
        logger.info(
            "Social page created/updated", 
            user_id=user_id, 
            platform=platform, 
            page_id=page.id
        )
        
        return page
    
    def create_social_page_metric(
        self, social_page_id: int, metric_date: date, data: Dict
    ) -> SocialPageMetric:
        """
        Create social page metric
        
        Args:
            social_page_id (int): Social page ID
            metric_date (date): Metric date
            data (Dict): Metric data
        
        Returns:
            SocialPageMetric: Created social page metric
        """
        # Check if metric exists for this date
        existing_metric = (
            self.db.query(SocialPageMetric)
            .filter(
                SocialPageMetric.social_page_id == social_page_id,
                SocialPageMetric.date == metric_date
            )
            .first()
        )
        
        # If metric exists, update it
        if existing_metric:
            # Update metric attributes
            for key, value in data.items():
                if hasattr(existing_metric, key):
                    setattr(existing_metric, key, value)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_metric)
            
            logger.info(
                "Social page metric updated", 
                social_page_id=social_page_id, 
                date=metric_date
            )
            
            return existing_metric
        
        # Otherwise, create new metric
        metric = SocialPageMetric(
            social_page_id=social_page_id,
            date=metric_date,
            **data
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        
        logger.info(
            "Social page metric created", 
            social_page_id=social_page_id, 
            date=metric_date
        )
        
        return metric
    
    def create_social_page_engagement(
        self, social_page_id: int, engagement_date: date, data: Dict
    ) -> SocialPageEngagement:
        """
        Create social page engagement
        
        Args:
            social_page_id (int): Social page ID
            engagement_date (date): Engagement date
            data (Dict): Engagement data
        
        Returns:
            SocialPageEngagement: Created social page engagement
        """
        # Check if engagement exists for this date
        existing_engagement = (
            self.db.query(SocialPageEngagement)
            .filter(
                SocialPageEngagement.social_page_id == social_page_id,
                SocialPageEngagement.date == engagement_date
            )
            .first()
        )
        
        # If engagement exists, update it
        if existing_engagement:
            # Update engagement attributes
            for key, value in data.items():
                if hasattr(existing_engagement, key):
                    setattr(existing_engagement, key, value)
            
            # Mark as updated
            existing_engagement.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_engagement)
            
            logger.info(
                "Social page engagement updated", 
                social_page_id=social_page_id, 
                date=engagement_date
            )
            
            return existing_engagement
        
        # Otherwise, create new engagement
        engagement = SocialPageEngagement(
            social_page_id=social_page_id,
            date=engagement_date,
            **data
        )
        
        self.db.add(engagement)
        self.db.commit()
        self.db.refresh(engagement)
        
        logger.info(
            "Social page engagement created", 
            social_page_id=social_page_id, 
            date=engagement_date
        )
        
        return engagement
    
    def create_social_page_growth(
        self, social_page_id: int, growth_date: date, data: Dict
    ) -> SocialPageGrowth:
        """
        Create social page growth
        
        Args:
            social_page_id (int): Social page ID
            growth_date (date): Growth date
            data (Dict): Growth data
        
        Returns:
            SocialPageGrowth: Created social page growth
        """
        # Check if growth exists for this date
        existing_growth = (
            self.db.query(SocialPageGrowth)
            .filter(
                SocialPageGrowth.social_page_id == social_page_id,
                SocialPageGrowth.date == growth_date
            )
            .first()
        )
        
        # If growth exists, update it
        if existing_growth:
            # Update growth attributes
            for key, value in data.items():
                if hasattr(existing_growth, key):
                    setattr(existing_growth, key, value)
            
            # Mark as updated
            existing_growth.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_growth)
            
            logger.info(
                "Social page growth updated", 
                social_page_id=social_page_id, 
                date=growth_date
            )
            
            return existing_growth
        
        # Otherwise, create new growth
        growth = SocialPageGrowth(
            social_page_id=social_page_id,
            date=growth_date,
            is_goal=False,  # This is historical data, not a goal
            **data
        )
        
        self.db.add(growth)
        self.db.commit()
        self.db.refresh(growth)
        
        logger.info(
            "Social page growth created", 
            social_page_id=social_page_id, 
            date=growth_date
        )
        
        return growth
    
    def create_social_page_reach(
        self, social_page_id: int, reach_date: date, data: Dict
    ) -> SocialPageReach:
        """
        Create social page reach
        
        Args:
            social_page_id (int): Social page ID
            reach_date (date): Reach date
            data (Dict): Reach data
        
        Returns:
            SocialPageReach: Created social page reach
        """
        # Check if reach exists for this date
        existing_reach = (
            self.db.query(SocialPageReach)
            .filter(
                SocialPageReach.social_page_id == social_page_id,
                SocialPageReach.date == reach_date
            )
            .first()
        )
        
        # If reach exists, update it
        if existing_reach:
            # Update reach attributes
            for key, value in data.items():
                if hasattr(existing_reach, key):
                    setattr(existing_reach, key, value)
            
            # Mark as updated
            existing_reach.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_reach)
            
            logger.info(
                "Social page reach updated", 
                social_page_id=social_page_id, 
                date=reach_date
            )
            
            return existing_reach
        
        # Otherwise, create new reach
        reach = SocialPageReach(
            social_page_id=social_page_id,
            date=reach_date,
            **data
        )
        
        self.db.add(reach)
        self.db.commit()
        self.db.refresh(reach)
        
        logger.info(
            "Social page reach created", 
            social_page_id=social_page_id, 
            date=reach_date
        )
        
        return reach
    
    def create_social_page_score(
        self, social_page_id: int, score_date: date, data: Dict
    ) -> SocialPageScore:
        """
        Create social page score
        
        Args:
            social_page_id (int): Social page ID
            score_date (date): Score date
            data (Dict): Score data
        
        Returns:
            SocialPageScore: Created social page score
        """
        # Check if score exists for this date
        existing_score = (
            self.db.query(SocialPageScore)
            .filter(
                SocialPageScore.social_page_id == social_page_id,
                SocialPageScore.date == score_date
            )
            .first()
        )
        
        # If score exists, update it
        if existing_score:
            # Update score attributes
            for key, value in data.items():
                if hasattr(existing_score, key):
                    setattr(existing_score, key, value)
            
            # Mark as updated
            existing_score.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_score)
            
            logger.info(
                "Social page score updated", 
                social_page_id=social_page_id, 
                date=score_date
            )
            
            return existing_score
        
        # Otherwise, create new score
        score = SocialPageScore(
            social_page_id=social_page_id,
            date=score_date,
            **data
        )
        
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        
        logger.info(
            "Social page score created", 
            social_page_id=social_page_id, 
            date=score_date
        )
        
        return score
    
    def create_or_update_social_page_post(
        self, social_page_id: int, platform: str, post_id: str, data: Dict
    ) -> SocialPagePost:
        """
        Create or update social page post
        
        Args:
            social_page_id (int): Social page ID
            platform (str): Social media platform
            post_id (str): Post ID
            data (Dict): Post data
        
        Returns:
            SocialPagePost: Created or updated social page post
        """
        # Check if post exists
        existing_post = (
            self.db.query(SocialPagePost)
            .filter(SocialPagePost.post_id == post_id)
            .first()
        )
        
        # If post exists, update it
        if existing_post:
            # Update post attributes
            for key, value in data.items():
                if hasattr(existing_post, key):
                    setattr(existing_post, key, value)
            
            # Mark as updated
            existing_post.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_post)
            
            logger.info(
                "Social page post updated", 
                platform=platform, 
                post_id=post_id
            )
            
            return existing_post
        
        # Otherwise, create new post
        post = SocialPagePost(
            social_page_id=social_page_id,
            platform=platform,
            post_id=post_id,
            **data
        )
        
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        
        logger.info(
            "Social page post created", 
            platform=platform, 
            post_id=post_id
        )
        
        return post
    
    def create_social_page_post_comment(
        self, post_id: int, platform: str, comment_id: str, data: Dict
    ) -> SocialPagePostComment:
        """
        Create social page post comment
        
        Args:
            post_id (int): Post ID
            platform (str): Social media platform
            comment_id (str): Comment ID
            data (Dict): Comment data
        
        Returns:
            SocialPagePostComment: Created social page post comment
        """
        # Check if comment exists
        existing_comment = (
            self.db.query(SocialPagePostComment)
            .filter(SocialPagePostComment.comment_id == comment_id)
            .first()
        )
        
        # If comment exists, update it
        if existing_comment:
            # Update comment attributes
            for key, value in data.items():
                if hasattr(existing_comment, key):
                    setattr(existing_comment, key, value)
            
            # Mark as updated
            existing_comment.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(existing_comment)
            
            logger.info(
                "Social page post comment updated", 
                platform=platform, 
                comment_id=comment_id
            )
            
            return existing_comment
        
        # Otherwise, create new comment
        comment = SocialPagePostComment(
            post_id=post_id,
            platform=platform,
            comment_id=comment_id,
            **data
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        logger.info(
            "Social page post comment created", 
            platform=platform, 
            comment_id=comment_id
        )
        
        return comment
    
    def calculate_engagement_rate(self, followers: int, engagement: int) -> float:
        """
        Calculate engagement rate
        
        Args:
            followers (int): Number of followers
            engagement (int): Total engagement (likes + comments + shares)
        
        Returns:
            float: Engagement rate as a percentage
        """
        if followers <= 0:
            return 0.0
        
        return (engagement / followers) * 100
    
    def calculate_growth_rate(self, current: int, previous: int) -> float:
        """
        Calculate growth rate
        
        Args:
            current (int): Current value
            previous (int): Previous value
        
        Returns:
            float: Growth rate as a percentage
        """
        if previous <= 0:
            return 0.0
        
        return ((current - previous) / previous) * 100
    
    def calculate_projected_followers(
        self, current_followers: int, growth_rate: float, days: int
    ) -> int:
        """
        Calculate projected followers
        
        Args:
            current_followers (int): Current followers count
            growth_rate (float): Daily growth rate as a percentage
            days (int): Number of days to project
        
        Returns:
            int: Projected followers count
        """
        # Convert growth rate from percentage to decimal
        daily_growth_decimal = growth_rate / 100
        
        # Calculate using compound growth formula
        projected = current_followers * ((1 + daily_growth_decimal) ** days)
        
        return int(projected)
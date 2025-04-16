from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import structlog
from sqlalchemy.orm import Session
from app.worker import celery
from app.utils.errors import SocialTokenError, NotFoundError
from app.services.sync.base import BaseSyncService

# Set up logger
logger = structlog.get_logger("analisaai-sync")

class InstagramSyncService(BaseSyncService):
    """Service for syncing Instagram data"""
    
    async def sync_profile(self, user_id: int) -> Dict:
        """
        Sync Instagram profile for a user
        
        Args:
            user_id (int): User ID
        
        Returns:
            Dict: Sync result
        
        Raises:
            SocialTokenError: If token not found or expired
            NotFoundError: If user not found
        """
        # Get user
        user = self.get_user(user_id)
        
        # Get Instagram username
        username = user.instagram_username
        if not username:
            raise SocialTokenError("User has no Instagram username configured")
        
        logger.info("Syncing Instagram profile", user_id=user_id, username=username)
        
        # Get Instagram data from Apify
        profile_data = await self.apify_service.get_instagram_profile(username)
        
        # Transform data to SocialPage format
        page_data = {
            "username": profile_data.get("username", username),
            "full_name": profile_data.get("fullName"),
            "profile_url": f"https://www.instagram.com/{username}/",
            "profile_image": profile_data.get("profilePicture"),
            "bio": profile_data.get("biography"),
            "followers_count": profile_data.get("followersCount", 0),
            "following_count": profile_data.get("followsCount", 0),
            "posts_count": profile_data.get("postsCount", 0),
        }
        
        # Create or update social page
        page = self.create_or_update_social_page(user_id, "instagram", page_data)
        
        # Fetch post data for calculating engagement
        posts_data = await self.apify_service.get_instagram_posts(username, limit=20)
        
        # Create metric records
        today = date.today()
        
        # Calculate engagement metrics
        total_likes = 0
        total_comments = 0
        total_posts = len(posts_data)
        
        for post in posts_data:
            total_likes += post.get("likesCount", 0)
            total_comments += post.get("commentsCount", 0)
            
            # Create or update post
            post_data = {
                "content": post.get("caption", ""),
                "post_url": post.get("url"),
                "media_url": post.get("displayUrl"),
                "posted_at": datetime.strptime(post.get("timestamp", ""), "%Y-%m-%dT%H:%M:%S.%fZ") if post.get("timestamp") else None,
                "content_type": post.get("type", "image"),
                "likes_count": post.get("likesCount", 0),
                "comments_count": post.get("commentsCount", 0),
            }
            
            # Calculate engagement rate for the post
            post_engagement = post_data["likes_count"] + post_data["comments_count"]
            post_data["engagement_rate"] = self.calculate_engagement_rate(page.followers_count, post_engagement)
            
            # Create or update post
            self.create_or_update_social_page_post(
                page.id, "instagram", post.get("id"), post_data
            )
        
        # Calculate average engagement per post
        avg_likes_per_post = total_likes / total_posts if total_posts > 0 else 0
        avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
        
        # Calculate total engagement
        total_engagement = total_likes + total_comments
        
        # Calculate engagement rate
        engagement_rate = self.calculate_engagement_rate(page.followers_count, total_engagement)
        
        # Update page with engagement rate
        page.engagement_rate = engagement_rate
        self.db.commit()
        
        # Create metrics
        metric_data = {
            "followers": page.followers_count,
            "engagement": engagement_rate,
            "posts": page.posts_count,
            "likes": total_likes,
            "comments": total_comments,
        }
        self.create_social_page_metric(page.id, today, metric_data)
        
        # Create engagement record
        engagement_data = {
            "posts_count": total_posts,
            "avg_likes_per_post": avg_likes_per_post,
            "avg_comments_per_post": avg_comments_per_post,
            "engagement_rate": engagement_rate,
            "total_likes": total_likes,
            "total_comments": total_comments,
        }
        self.create_social_page_engagement(page.id, today, engagement_data)
        
        # Get previous metrics for growth calculation
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Get yesterday's data
        yesterday_growth = (
            self.db.query(SocialPageGrowth)
            .filter(
                SocialPageGrowth.social_page_id == page.id,
                SocialPageGrowth.date == yesterday
            )
            .first()
        )
        
        # Calculate growth metrics
        new_followers_daily = 0
        daily_growth_rate = 0.0
        
        if yesterday_growth:
            new_followers_daily = page.followers_count - yesterday_growth.followers_count
            daily_growth_rate = self.calculate_growth_rate(page.followers_count, yesterday_growth.followers_count)
        
        # Calculate projected followers
        projected_followers_30d = self.calculate_projected_followers(
            page.followers_count, daily_growth_rate, 30
        )
        projected_followers_90d = self.calculate_projected_followers(
            page.followers_count, daily_growth_rate, 90
        )
        
        # Create growth record
        growth_data = {
            "followers_count": page.followers_count,
            "new_followers_daily": new_followers_daily,
            "daily_growth_rate": daily_growth_rate,
            "projected_followers_30d": projected_followers_30d,
            "projected_followers_90d": projected_followers_90d,
        }
        self.create_social_page_growth(page.id, today, growth_data)
        
        # Calculate score
        engagement_score = min(engagement_rate * 10, 100)  # Scale engagement rate to 0-100
        growth_score = min(daily_growth_rate * 5, 100)  # Scale growth rate to 0-100
        
        # Create score record
        score_data = {
            "engagement_score": engagement_score,
            "growth_score": growth_score,
            # Calculate overall score with weights
            "overall_score": (
                (engagement_score * 0.6) +
                (growth_score * 0.4)
            ),
        }
        self.create_social_page_score(page.id, today, score_data)
        
        # Return sync result
        return {
            "success": True,
            "platform": "instagram",
            "username": username,
            "followers": page.followers_count,
            "engagement_rate": engagement_rate,
            "message": "Instagram profile synced successfully",
        }

@celery.task(name="sync_instagram_profile")
def sync_instagram_profile(user_id: int) -> Dict:
    """Celery task for syncing Instagram profile"""
    from app.config.database import SessionLocal
    import asyncio
    try:
        with SessionLocal() as db:
            service = InstagramSyncService(db)
            try:
                # Garantir execução do método async
                result = asyncio.run(service.sync_profile(user_id))
                # Padronizar retorno
                if not result.get("status"):
                    result["status"] = "ok" if result.get("success") else "error"
                return result
            except Exception as e:
                logger.error("Instagram sync failed", user_id=user_id, error=str(e))
                return {
                    "status": "error",
                    "success": False,
                    "platform": "instagram",
                    "error": str(e),
                    "message": "Instagram sync failed",
                }
    except Exception as e:
        logger.error("Instagram sync failed (DB error)", user_id=user_id, error=str(e))
        return {
            "status": "error",
            "success": False,
            "platform": "instagram",
            "error": str(e),
            "message": "Instagram sync failed (DB error)",
        }
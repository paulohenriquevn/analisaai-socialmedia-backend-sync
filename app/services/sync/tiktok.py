from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import structlog
from sqlalchemy.orm import Session
from app.worker import celery
from app.utils.errors import SocialTokenError, NotFoundError
from app.services.sync.base import BaseSyncService

# Set up logger
logger = structlog.get_logger("analisaai-sync")

class TikTokSyncService(BaseSyncService):
    """Service for syncing TikTok data"""
    
    async def sync_profile(self, user_id: int) -> Dict:
        """
        Sync TikTok profile for a user
        
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
        
        # Get TikTok username
        username = user.tiktok_username
        if not username:
            raise SocialTokenError("User has no TikTok username configured")
        
        logger.info("Syncing TikTok profile", user_id=user_id, username=username)
        
        # Get TikTok data from Apify
        profile_data = await self.apify_service.get_tiktok_profile(username)
        
        # Extract profile information
        profile_info = profile_data.get("user", {})
        stats = profile_info.get("stats", {})
        
        # Transform data to SocialPage format
        page_data = {
            "username": profile_info.get("uniqueId", username),
            "full_name": profile_info.get("nickname"),
            "profile_url": f"https://www.tiktok.com/@{username}/",
            "profile_image": profile_info.get("avatarMedium"),
            "bio": profile_info.get("signature"),
            "followers_count": stats.get("followerCount", 0),
            "following_count": stats.get("followingCount", 0),
            "posts_count": stats.get("videoCount", 0),
        }
        
        # Create or update social page
        page = self.create_or_update_social_page(user_id, "tiktok", page_data)
        
        # Get videos for engagement calculation
        videos = profile_data.get("items", [])
        
        # Calculate engagement metrics
        total_likes = 0
        total_comments = 0
        total_shares = 0
        total_views = 0
        total_posts = len(videos)
        
        for video in videos:
            # Extract video statistics
            video_stats = video.get("stats", {})
            
            # Get engagement metrics
            video_likes = video_stats.get("diggCount", 0)
            video_comments = video_stats.get("commentCount", 0)
            video_shares = video_stats.get("shareCount", 0)
            video_views = video_stats.get("playCount", 0)
            
            # Add to totals
            total_likes += video_likes
            total_comments += video_comments
            total_shares += video_shares
            total_views += video_views
            
            # Create or update post
            video_info = video.get("video", {})
            created_time = int(video.get("createTime", 0))
            
            post_data = {
                "content": video.get("desc", ""),
                "post_url": f"https://www.tiktok.com/@{username}/video/{video.get('id')}",
                "media_url": video_info.get("downloadAddr"),
                "posted_at": datetime.fromtimestamp(created_time) if created_time else None,
                "content_type": "video",
                "likes_count": video_likes,
                "comments_count": video_comments,
                "shares_count": video_shares,
                "views_count": video_views,
            }
            
            # Calculate engagement rate for the video
            video_engagement = video_likes + video_comments + video_shares
            post_data["engagement_rate"] = self.calculate_engagement_rate(page.followers_count, video_engagement)
            
            # Create or update post
            self.create_or_update_social_page_post(
                page.id, "tiktok", video.get("id"), post_data
            )
        
        # Calculate average engagement per post
        avg_likes_per_post = total_likes / total_posts if total_posts > 0 else 0
        avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
        avg_shares_per_post = total_shares / total_posts if total_posts > 0 else 0
        
        # Calculate total engagement
        total_engagement = total_likes + total_comments + total_shares
        
        # Calculate engagement rate
        engagement_rate = self.calculate_engagement_rate(page.followers_count, total_engagement)
        
        # Update page with engagement rate
        page.engagement_rate = engagement_rate
        self.db.commit()
        
        # Get today's date
        today = date.today()
        
        # Create metrics
        metric_data = {
            "followers": page.followers_count,
            "engagement": engagement_rate,
            "posts": page.posts_count,
            "likes": total_likes,
            "comments": total_comments,
            "shares": total_shares,
            "views": total_views,
        }
        self.create_social_page_metric(page.id, today, metric_data)
        
        # Create engagement record
        engagement_data = {
            "posts_count": total_posts,
            "avg_likes_per_post": avg_likes_per_post,
            "avg_comments_per_post": avg_comments_per_post,
            "avg_shares_per_post": avg_shares_per_post,
            "engagement_rate": engagement_rate,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "video_views": total_views,
        }
        self.create_social_page_engagement(page.id, today, engagement_data)
        
        # Get previous metrics for growth calculation
        yesterday = today - timedelta(days=1)
        
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
        
        # Calculate reach data
        reach_data = {
            "impressions": total_views,
            "reach": int(total_views * 0.8),  # Estimate unique viewers as 80% of total views
        }
        self.create_social_page_reach(page.id, today, reach_data)
        
        # Calculate score
        engagement_score = min(engagement_rate * 10, 100)  # Scale engagement rate to 0-100
        growth_score = min(daily_growth_rate * 5, 100)  # Scale growth rate to 0-100
        reach_score = min(total_views / 1000, 100)  # Scale views to 0-100
        
        # Create score record
        score_data = {
            "engagement_score": engagement_score,
            "growth_score": growth_score,
            "reach_score": reach_score,
            # Calculate overall score with weights
            "overall_score": (
                (engagement_score * 0.5) +
                (growth_score * 0.3) +
                (reach_score * 0.2)
            ),
            "engagement_weight": 0.5,
            "growth_weight": 0.3,
            "reach_weight": 0.2,
        }
        self.create_social_page_score(page.id, today, score_data)
        
        # Return sync result
        return {
            "success": True,
            "platform": "tiktok",
            "username": username,
            "followers": page.followers_count,
            "engagement_rate": engagement_rate,
            "message": "TikTok profile synced successfully",
        }

@celery.task(name="sync_tiktok_profile")
def sync_tiktok_profile(user_id: int) -> Dict:
    """Celery task for syncing TikTok profile"""
    from app.config.database import SessionLocal
    import asyncio
    try:
        with SessionLocal() as db:
            service = TikTokSyncService(db)
            try:
                # Garantir execução do método async, se necessário
                result = asyncio.run(service.sync_profile(user_id))
                if not result.get("status"):
                    result["status"] = "ok" if result.get("success") else "error"
                return result
            except Exception as e:
                logger.error("TikTok sync failed", user_id=user_id, error=str(e))
                return {
                    "status": "error",
                    "success": False,
                    "platform": "tiktok",
                    "error": str(e),
                    "message": "TikTok sync failed",
                }
    except Exception as e:
        logger.error("TikTok sync failed (DB error)", user_id=user_id, error=str(e))
        return {
            "status": "error",
            "success": False,
            "platform": "tiktok",
            "error": str(e),
            "message": "TikTok sync failed (DB error)",
        }
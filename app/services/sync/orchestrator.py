from typing import Dict, List, Optional
import structlog
from sqlalchemy.orm import Session
from app.models.user import User
from app.worker import celery
from app.utils.errors import SocialTokenError, NotFoundError
from app.services.sync.instagram import sync_instagram_profile
from app.services.sync.facebook import sync_facebook_profile
from app.services.sync.tiktok import sync_tiktok_profile

# Set up logger
logger = structlog.get_logger("analisaai-sync")

# Central mapping for platform sync tasks
PLATFORM_SYNC_TASKS = {
    "instagram": sync_instagram_profile,
    "facebook": sync_facebook_profile,
    "tiktok": sync_tiktok_profile,
}

class SyncOrchestrator:
    """Orchestrates the synchronization of social media data.
    
    To add a new platform:
      1. Implemente a função de sync e registre-a em PLATFORM_SYNC_TASKS.
      2. Adicione o atributo correspondente no modelo User ou, preferencialmente, utilize uma tabela de contas vinculadas.
    """
    
    def __init__(self, db: Session):
        """
        Initialize sync orchestrator
        
        Args:
            db (Session): Database session
        """
        self.db = db
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users
        
        Returns:
            List[User]: List of active users
        """
        return self.db.query(User).filter(User.is_active == True).all()
    
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
    
    def get_platforms_for_user(self, user: User) -> List[str]:
        """
        Get platforms for user.
        Futuramente, refatore para buscar plataformas a partir de uma tabela de contas vinculadas.
        """
        platforms = []
        if getattr(user, "instagram_username", None):
            platforms.append("instagram")
        if getattr(user, "facebook_username", None):
            platforms.append("facebook")
        if getattr(user, "tiktok_username", None):
            platforms.append("tiktok")
        return platforms
    
    def sync_user(self, user_id: int) -> Dict:
        """
        Sync social media data for a user
        """
        logger.info("Syncing social media data for user", user_id=user_id)
        try:
            user = self.get_user(user_id)
        except NotFoundError as e:
            logger.error("User not found", user_id=user_id, error=str(e))
            return {
                "user_id": user_id,
                "status": "error",
                "error": str(e),
                "message": "User not found"
            }
        platforms = self.get_platforms_for_user(user)
        results = {}
        for platform in platforms:
            sync_task = PLATFORM_SYNC_TASKS.get(platform)
            if not sync_task:
                logger.warning("No sync task registered for platform", platform=platform)
                results[platform] = {"status": "skipped", "message": "No sync task registered"}
                continue
            try:
                task = sync_task.delay(user_id)
                results[platform] = {"task_id": task.id, "status": "queued"}
            except Exception as e:
                logger.error(
                    f"Failed to queue {platform} sync task",
                    user_id=user_id,
                    error=str(e)
                )
                results[platform] = {"status": "error", "error": str(e)}
        return {
            "user_id": user_id,
            "platforms": platforms,
            "results": results,
            "status": "ok" if all(v.get("status") == "queued" for v in results.values()) else "partial_error"
        }
    
    def sync_all_users(self) -> Dict:
        """
        Sync social media data for all active users
        """
        logger.info("Syncing social media data for all active users")
        users = self.get_active_users()
        results = []
        for user in users:
            try:
                result = self.sync_user(user.id)
                results.append(result)
            except Exception as e:
                logger.error(
                    "Failed to sync user",
                    user_id=user.id,
                    error=str(e)
                )
                results.append({
                    "user_id": user.id,
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to sync user"
                })
        return {
            "total_users": len(users),
            "results": results,
            "status": "ok" if all(r.get("status") == "ok" for r in results) else "partial_error"
        }

@celery.task(name="sync_all_users")
def sync_all_users() -> Dict:
    """Celery task for syncing all users"""
    from app.config.database import SessionLocal
    # Use context manager for DB session
    try:
        with SessionLocal() as db:
            orchestrator = SyncOrchestrator(db)
            result = orchestrator.sync_all_users()
            return result
    except Exception as e:
        logger.error("Failed to sync all users", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to sync all users"
        }
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.config.database import get_db
from app.utils.auth import get_current_user, get_admin_user
from app.utils.errors import NotFoundError, SocialTokenError
from app.services.sync.orchestrator import SyncOrchestrator

# Set up logger
logger = structlog.get_logger("analisaai-sync")

# Create router
router = APIRouter()

@router.post("/user/{user_id}")
async def sync_user(
    user_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync social media data for a specific user
    
    Args:
        user_id (int): User ID
        current_user (Dict): Current authenticated user
        db (Session): Database session
    
    Returns:
        Dict: Sync result
    """
    # Check if current user is admin or the requested user
    if not current_user.get("is_admin", False) and str(current_user.get("id")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only sync your own social media data",
        )
    # Exemplo: Para proteger endpoint por outra role, crie um Depends customizado:
    # from fastapi import Depends
    # def get_manager_user(current_user: Dict = Depends(get_current_user)):
    #     if "manager" not in current_user["roles"]:
    #         raise HTTPException(status_code=403, detail="Manager role required")
    #     return current_user
    
    try:
        # Create sync orchestrator
        orchestrator = SyncOrchestrator(db)
        
        # Sync user
        result = orchestrator.sync_user(user_id)
        
        return result
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    except SocialTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    except Exception as e:
        logger.error("Sync error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync user: {str(e)}",
        )

@router.post("/all-users")
async def sync_all_users(
    admin_user: Dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sync social media data for all active users
    
    Args:
        admin_user (Dict): Admin user
        db (Session): Database session
    
    Returns:
        Dict: Sync result
    """
    try:
        # Create sync orchestrator
        orchestrator = SyncOrchestrator(db)
        
        # Sync all users
        result = orchestrator.sync_all_users()
        
        return result
    
    except Exception as e:
        logger.error("Sync all users error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync all users: {str(e)}",
        )
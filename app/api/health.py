from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from redis import Redis
import structlog

from app.config.database import get_db
from app.config.settings import settings
from app.utils.errors import APIError

# Create router
router = APIRouter()

# Set up logger
logger = structlog.get_logger("analisaai-sync")

@router.get("/ping")
async def ping():
    """
    Simple ping endpoint to check if API is running
    """
    return {"status": "ok", "service": "analisaai-sync"}

@router.get("/status")
async def status_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check to verify API, database, and Redis connectivity
    
    Args:
        db (Session): Database session
    
    Returns:
        dict: Health status of various components
    """
    status_info = {
        "service": "analisaai-sync",
        "version": "1.0.0",
        "database": "unknown",
        "redis": "unknown",
        "status": "degraded",
    }
    
    # Check database connection
    try:
        # Execute a simple query to check DB connection
        db.execute(text("SELECT 1"))
        status_info["database"] = "connected"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        status_info["database"] = "error"
    
    # Check Redis connection
    try:
        # Create Redis connection
        redis = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        # Ping Redis
        if redis.ping():
            status_info["redis"] = "connected"
        redis.close()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        status_info["redis"] = "error"
    
    # Determine overall status
    if status_info["database"] == "connected" and status_info["redis"] == "connected":
        status_info["status"] = "ok"
    
    # Set appropriate status code
    response_status = status.HTTP_200_OK if status_info["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        content=status_info,
        status_code=response_status,
    )
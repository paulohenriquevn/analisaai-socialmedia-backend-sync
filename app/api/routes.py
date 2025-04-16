from fastapi import APIRouter
from app.api.sync import router as sync_router
from app.api.health import router as health_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(sync_router, prefix="/sync", tags=["sync"])
router.include_router(health_router, prefix="/health", tags=["health"])
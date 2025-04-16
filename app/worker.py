import os
from celery import Celery
import structlog
from app.config.settings import settings

# Set up logger
logger = structlog.get_logger("analisaai-sync")

# Create Celery app
celery = Celery(
    "analisaai-sync",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
)

# Auto-discover tasks
celery.autodiscover_tasks(['app.services.sync'])

@celery.task(name="test_task")
def test_task():
    """Test task to verify Celery is working"""
    logger.info("Test task executed successfully")
    return {"status": "success"}
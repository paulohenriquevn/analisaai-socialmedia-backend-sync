from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config.settings import settings
from app.utils.logger import setup_logging
from app.config.database import Base, engine

# Setup logging
logger = setup_logging()

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title="Analisa.ai Social Media Sync Service",
    description="Backend service for syncing social media data from different platforms",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "analisaai-sync", "version": "1.0.0"}
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function to get a database session
    
    Yields:
        db: SQLAlchemy DB session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
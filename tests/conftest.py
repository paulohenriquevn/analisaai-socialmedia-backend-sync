import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.config.settings import settings
from app.utils.encryption import encrypt_value
from common.user import User
from common.social_media import SocialToken

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine):
    """Create a new database session for a test"""
    # Connect to database
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()
    
    yield session
    
    # Roll back transaction and close connection
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        instagram_username="testuser_ig",
        facebook_username="testuser_fb",
        tiktok_username="testuser_tiktok",
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def test_social_token(db_session, test_user):
    """Create a test social token"""
    token = SocialToken(
        user_id=test_user.id,
        platform="instagram",
        access_token=encrypt_value("mock_access_token"),
    )
    db_session.add(token)
    db_session.commit()
    
    return token
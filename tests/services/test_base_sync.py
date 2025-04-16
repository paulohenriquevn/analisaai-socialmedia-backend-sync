import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from app.services.sync.base import BaseSyncService
from app.utils.errors import NotFoundError, SocialTokenError
from common.social_media import SocialPage, SocialToken

@pytest.fixture
def base_sync_service(db_session):
    """Create a base sync service instance"""
    return BaseSyncService(db_session)

class TestBaseSyncService:
    """Tests for BaseSyncService"""
    
    def test_get_user_success(self, base_sync_service, test_user):
        """Test get_user success"""
        # Call the method
        user = base_sync_service.get_user(test_user.id)
        
        # Assert result
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    def test_get_user_not_found(self, base_sync_service):
        """Test get_user not found"""
        # Call the method and expect exception
        with pytest.raises(NotFoundError):
            base_sync_service.get_user(999)
    
    def test_get_social_token_success(self, base_sync_service, test_user, test_social_token):
        """Test get_social_token success"""
        # Call the method
        token = base_sync_service.get_social_token(test_user.id, "instagram")
        
        # Assert result
        assert token.id == test_social_token.id
        assert token.user_id == test_user.id
        assert token.platform == "instagram"
    
    def test_get_social_token_not_found(self, base_sync_service, test_user):
        """Test get_social_token not found"""
        # Call the method and expect exception
        with pytest.raises(SocialTokenError):
            base_sync_service.get_social_token(test_user.id, "facebook")
    
    def test_create_or_update_social_page_create(self, base_sync_service, test_user, db_session):
        """Test create_or_update_social_page create"""
        # Test data
        platform = "instagram"
        data = {
            "username": "testuser_ig",
            "full_name": "Test User",
            "profile_url": "https://instagram.com/testuser_ig",
            "followers_count": 1000,
        }
        
        # Call the method
        page = base_sync_service.create_or_update_social_page(test_user.id, platform, data)
        
        # Assert result
        assert page.id is not None
        assert page.user_id == test_user.id
        assert page.platform == platform
        assert page.username == data["username"]
        assert page.full_name == data["full_name"]
        assert page.profile_url == data["profile_url"]
        assert page.followers_count == data["followers_count"]
        
        # Verify page was added to database
        db_page = db_session.query(SocialPage).filter(SocialPage.id == page.id).first()
        assert db_page is not None
    
    def test_create_or_update_social_page_update(self, base_sync_service, test_user, db_session):
        """Test create_or_update_social_page update"""
        # Create existing page
        existing_page = SocialPage(
            user_id=test_user.id,
            platform="instagram",
            username="testuser_ig",
            full_name="Original Name",
            followers_count=500,
        )
        db_session.add(existing_page)
        db_session.commit()
        
        # Test data
        platform = "instagram"
        data = {
            "username": "testuser_ig",
            "full_name": "Updated Name",
            "followers_count": 1000,
        }
        
        # Call the method
        page = base_sync_service.create_or_update_social_page(test_user.id, platform, data)
        
        # Assert result
        assert page.id == existing_page.id
        assert page.user_id == test_user.id
        assert page.platform == platform
        assert page.username == data["username"]
        assert page.full_name == data["full_name"]
        assert page.followers_count == data["followers_count"]
    
    def test_calculate_engagement_rate(self, base_sync_service):
        """Test calculate_engagement_rate"""
        # Test cases
        test_cases = [
            {"followers": 1000, "engagement": 100, "expected": 10.0},
            {"followers": 1000, "engagement": 0, "expected": 0.0},
            {"followers": 0, "engagement": 100, "expected": 0.0},
        ]
        
        for case in test_cases:
            result = base_sync_service.calculate_engagement_rate(
                case["followers"], case["engagement"]
            )
            assert result == case["expected"]
    
    def test_calculate_growth_rate(self, base_sync_service):
        """Test calculate_growth_rate"""
        # Test cases
        test_cases = [
            {"current": 1100, "previous": 1000, "expected": 10.0},
            {"current": 1000, "previous": 1000, "expected": 0.0},
            {"current": 900, "previous": 1000, "expected": -10.0},
            {"current": 1000, "previous": 0, "expected": 0.0},
        ]
        
        for case in test_cases:
            result = base_sync_service.calculate_growth_rate(
                case["current"], case["previous"]
            )
            assert result == case["expected"]
    
    def test_calculate_projected_followers(self, base_sync_service):
        """Test calculate_projected_followers"""
        # Test cases
        test_cases = [
            {"current": 1000, "growth_rate": 1.0, "days": 30, "expected": 1348},
            {"current": 1000, "growth_rate": 0.0, "days": 30, "expected": 1000},
            {"current": 1000, "growth_rate": -1.0, "days": 30, "expected": 740},
        ]
        
        for case in test_cases:
            result = base_sync_service.calculate_projected_followers(
                case["current"], case["growth_rate"], case["days"]
            )
            assert result == case["expected"]
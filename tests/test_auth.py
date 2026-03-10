"""
Tests for Authentication.
"""

import pytest
from open_grace.security.auth import AuthManager, User


class TestAuthManager:
    """Test suite for AuthManager."""
    
    @pytest.fixture
    def auth(self):
        """Create auth manager for testing."""
        return AuthManager(secret_key="test_secret_key_for_testing")
    
    def test_create_user(self, auth):
        """Test user creation."""
        user = auth.create_user("testuser", "test@example.com")
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.id is not None
    
    def test_get_user(self, auth):
        """Test retrieving user by ID."""
        created = auth.create_user("testuser", "test@example.com")
        retrieved = auth.get_user(created.id)
        
        assert retrieved is not None
        assert retrieved.username == "testuser"
    
    def test_get_user_by_username(self, auth):
        """Test retrieving user by username."""
        auth.create_user("testuser", "test@example.com")
        user = auth.get_user_by_username("testuser")
        
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_create_api_key(self, auth):
        """Test API key creation."""
        user = auth.create_user("testuser", "test@example.com")
        api_key, key_id = auth.create_api_key(user.id, "Test Key")
        
        assert api_key.startswith("og_")
        assert key_id is not None
    
    def test_validate_api_key(self, auth):
        """Test API key validation."""
        user = auth.create_user("testuser", "test@example.com")
        api_key, _ = auth.create_api_key(user.id, "Test Key")
        
        validated_user = auth.validate_api_key(api_key)
        assert validated_user is not None
        assert validated_user.id == user.id
    
    def test_validate_invalid_api_key(self, auth):
        """Test validation of invalid API key."""
        result = auth.validate_api_key("invalid_key")
        assert result is None
    
    def test_revoke_api_key(self, auth):
        """Test API key revocation."""
        user = auth.create_user("testuser", "test@example.com")
        api_key, key_id = auth.create_api_key(user.id, "Test Key")
        
        # Revoke
        result = auth.revoke_api_key(key_id)
        assert result is True
        
        # Should no longer validate
        validated = auth.validate_api_key(api_key)
        assert validated is None
    
    def test_create_jwt_token(self, auth):
        """Test JWT token creation."""
        user = auth.create_user("testuser", "test@example.com")
        token = auth.create_jwt_token(user.id)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_validate_jwt_token(self, auth):
        """Test JWT token validation."""
        user = auth.create_user("testuser", "test@example.com")
        token = auth.create_jwt_token(user.id)
        
        payload = auth.validate_jwt_token(token)
        assert payload is not None
        assert payload["sub"] == user.id
    
    def test_validate_invalid_jwt(self, auth):
        """Test validation of invalid JWT."""
        payload = auth.validate_jwt_token("invalid.token.here")
        assert payload is None
    
    def test_list_api_keys(self, auth):
        """Test listing API keys."""
        user = auth.create_user("testuser", "test@example.com")
        auth.create_api_key(user.id, "Key 1")
        auth.create_api_key(user.id, "Key 2")
        
        keys = auth.list_api_keys(user_id=user.id)
        assert len(keys) == 2
    
    def test_delete_user(self, auth):
        """Test user deletion."""
        user = auth.create_user("testuser", "test@example.com")
        api_key, _ = auth.create_api_key(user.id, "Test Key")
        
        # Delete user
        result = auth.delete_user(user.id)
        assert result is True
        
        # User should be gone
        assert auth.get_user(user.id) is None
        # API key should be revoked
        assert auth.validate_api_key(api_key) is None
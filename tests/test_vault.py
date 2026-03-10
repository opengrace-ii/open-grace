"""
Tests for Secret Vault.
"""

import pytest
import tempfile
import os
from open_grace.security.vault import SecretVault


class TestSecretVault:
    """Test suite for SecretVault."""
    
    @pytest.fixture
    def vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = os.path.join(tmpdir, "test_vault")
            vault = SecretVault(vault_path=vault_path)
            yield vault
    
    def test_initialization(self, vault):
        """Test vault initialization."""
        assert vault is not None
        assert vault._initialized is False
    
    def test_unlock_with_password(self, vault):
        """Test unlocking vault with password."""
        result = vault.unlock_with_password("test_password")
        assert result is True
        assert vault._initialized is True
    
    def test_store_and_retrieve_secret(self, vault):
        """Test storing and retrieving secrets."""
        vault.unlock_with_password("test_password")
        
        # Store secret
        vault.store("api_key", "secret_value123")
        
        # Retrieve secret
        value = vault.get("api_key")
        assert value == "secret_value123"
    
    def test_retrieve_nonexistent_secret(self, vault):
        """Test retrieving a non-existent secret."""
        vault.unlock_with_password("test_password")
        
        value = vault.get("nonexistent")
        assert value is None
    
    def test_delete_secret(self, vault):
        """Test deleting a secret."""
        vault.unlock_with_password("test_password")
        
        vault.store("to_delete", "value")
        assert vault.get("to_delete") == "value"
        
        vault.delete("to_delete")
        assert vault.get("to_delete") is None
    
    def test_list_secrets(self, vault):
        """Test listing all secrets."""
        vault.unlock_with_password("test_password")
        
        vault.store("key1", "value1")
        vault.store("key2", "value2")
        
        secrets = vault.list_secrets()
        assert "key1" in secrets
        assert "key2" in secrets
    
    def test_persistence(self, vault):
        """Test that secrets persist across vault instances."""
        vault.unlock_with_password("test_password")
        vault.store("persistent", "data")
        
        # Create new vault instance with same path
        vault_path = vault.vault_path
        new_vault = SecretVault(vault_path=vault_path)
        new_vault.unlock_with_password("test_password")
        
        assert new_vault.get("persistent") == "data"
    
    def test_change_password(self, vault):
        """Test changing vault password."""
        vault.unlock_with_password("old_password")
        vault.store("secret", "value")
        
        # Change password
        result = vault.change_password("old_password", "new_password")
        assert result is True
        
        # Unlock with new password
        new_vault = SecretVault(vault_path=vault.vault_path)
        result = new_vault.unlock_with_password("new_password")
        assert result is True
        assert new_vault.get("secret") == "value"
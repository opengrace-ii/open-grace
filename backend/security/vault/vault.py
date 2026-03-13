"""
Secret Vault - Secure storage and retrieval of sensitive credentials.

This module provides a secure vault for storing API keys, passwords,
and other secrets. Secrets are encrypted at rest and never exposed
to LLM prompts or logs.
"""

import os
import json
import base64
import hashlib
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class SecretEntry:
    """A single secret entry in the vault."""
    key: str
    value: str
    category: str  # 'api_key', 'password', 'token', 'certificate', etc.
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}


class SecretVault:
    """
    Secure vault for storing and retrieving secrets.
    
    Features:
    - Encryption at rest using Fernet (AES-128)
    - Key derivation using PBKDF2
    - Categorized secret storage
    - Access logging
    - Never exposes secrets in logs or prompts
    
    Usage:
        vault = SecretVault()
        vault.set_secret("openai_api_key", "sk-...", category="api_key")
        api_key = vault.get_secret("openai_api_key")
    """
    
    def __init__(self, vault_path: Optional[str] = None, master_key: Optional[str] = None):
        """
        Initialize the secret vault.
        
        Args:
            vault_path: Path to the vault file. Defaults to ~/.open_grace/vault.enc
            master_key: Master key for encryption. If not provided, uses env var or generates one.
        """
        self.vault_path = vault_path or os.path.expanduser("~/.open_grace/vault.enc")
        self._master_key = master_key or os.environ.get("OPEN_GRACE_MASTER_KEY")
        self._secrets: Dict[str, SecretEntry] = {}
        self._access_log: List[Dict[str, Any]] = []
        
        # Ensure vault directory exists
        Path(self.vault_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self._cipher = self._initialize_cipher()
        
        # Load existing vault if present
        self._load_vault()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize the encryption cipher."""
        if not self._master_key:
            # Generate a key if none exists (for development only)
            # In production, this should fail and require a proper key
            self._master_key = Fernet.generate_key().decode()
            print("WARNING: No master key provided. Generated a temporary key.")
            print("Set OPEN_GRACE_MASTER_KEY environment variable for production.")
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"open_grace_vault_salt_v1",  # In production, use a unique salt per installation
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
        return Fernet(key)
    
    def _load_vault(self):
        """Load secrets from the vault file."""
        if not os.path.exists(self.vault_path):
            return
        
        try:
            with open(self.vault_path, 'rb') as f:
                encrypted_data = f.read()
            
            if encrypted_data:
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
                
                for key, entry_data in data.get("secrets", {}).items():
                    self._secrets[key] = SecretEntry(**entry_data)
        except Exception as e:
            print(f"Warning: Could not load vault: {e}")
            self._secrets = {}
    
    def _save_vault(self):
        """Save secrets to the vault file."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "secrets": {
                key: asdict(entry) for key, entry in self._secrets.items()
            }
        }
        
        encrypted_data = self._cipher.encrypt(json.dumps(data).encode())
        
        # Write atomically
        temp_path = self.vault_path + ".tmp"
        with open(temp_path, 'wb') as f:
            f.write(encrypted_data)
        os.replace(temp_path, self.vault_path)
        
        # Set restrictive permissions
        os.chmod(self.vault_path, 0o600)
    
    def _log_access(self, action: str, key: str, success: bool):
        """Log vault access for audit purposes."""
        self._access_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "key": key,
            "success": success
        })
        # Keep only last 1000 entries
        self._access_log = self._access_log[-1000:]
    
    def set_secret(self, key: str, value: str, category: str = "general", 
                   description: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a secret in the vault.
        
        Args:
            key: Unique identifier for the secret
            value: The secret value
            category: Category of the secret (api_key, password, token, etc.)
            description: Human-readable description
            metadata: Additional metadata
        """
        entry = SecretEntry(
            key=key,
            value=value,
            category=category,
            description=description,
            updated_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self._secrets[key] = entry
        self._save_vault()
        self._log_access("set", key, True)
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from the vault.
        
        Args:
            key: The secret identifier
            
        Returns:
            The secret value or None if not found
        """
        entry = self._secrets.get(key)
        if entry:
            self._log_access("get", key, True)
            return entry.value
        
        self._log_access("get", key, False)
        return None
    
    def get_secret_entry(self, key: str) -> Optional[SecretEntry]:
        """Get the full secret entry including metadata."""
        return self._secrets.get(key)
    
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret from the vault.
        
        Args:
            key: The secret identifier
            
        Returns:
            True if deleted, False if not found
        """
        if key in self._secrets:
            del self._secrets[key]
            self._save_vault()
            self._log_access("delete", key, True)
            return True
        
        self._log_access("delete", key, False)
        return False
    
    def list_secrets(self, category: Optional[str] = None) -> List[str]:
        """
        List all secret keys, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of secret keys
        """
        if category:
            return [k for k, v in self._secrets.items() if v.category == category]
        return list(self._secrets.keys())
    
    def list_by_category(self) -> Dict[str, List[str]]:
        """List secrets grouped by category."""
        result: Dict[str, List[str]] = {}
        for key, entry in self._secrets.items():
            if entry.category not in result:
                result[entry.category] = []
            result[entry.category].append(key)
        return result
    
    def has_secret(self, key: str) -> bool:
        """Check if a secret exists."""
        return key in self._secrets
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(v.category for v in self._secrets.values()))
    
    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get the access log (without secret values)."""
        return self._access_log.copy()
    
    def rotate_key(self, new_master_key: str):
        """
        Rotate the encryption key.
        
        Args:
            new_master_key: The new master key
        """
        # Re-encrypt with new key
        self._master_key = new_master_key
        self._cipher = self._initialize_cipher()
        self._save_vault()
        self._log_access("rotate_key", "*", True)
    
    def export_config(self, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export secrets for configuration (without values).
        
        Args:
            keys: Optional list of keys to export. If None, exports all.
            
        Returns:
            Dictionary with secret metadata (no values)
        """
        result = {}
        for k, v in self._secrets.items():
            if keys is None or k in keys:
                result[k] = {
                    "category": v.category,
                    "description": v.description,
                    "created_at": v.created_at,
                    "updated_at": v.updated_at,
                    "metadata": v.metadata
                }
        return result
    
    def mask_secret(self, value: str, visible_chars: int = 4) -> str:
        """
        Mask a secret for display purposes.
        
        Args:
            value: The secret value
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked string like "************abcd"
        """
        if len(value) <= visible_chars:
            return "*" * len(value)
        return "*" * (len(value) - visible_chars) + value[-visible_chars:]


# Global vault instance
_vault: Optional[SecretVault] = None


def get_vault() -> SecretVault:
    """Get the global vault instance."""
    global _vault
    if _vault is None:
        _vault = SecretVault()
    return _vault


def set_vault(vault: SecretVault):
    """Set the global vault instance."""
    global _vault
    _vault = vault
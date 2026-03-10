"""
Vault Providers - Different backends for secret storage.

This module provides various backends for storing secrets:
- FileVaultProvider: Local encrypted file storage
- Future: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os


@dataclass
class SecretMetadata:
    """Metadata for a secret."""
    key: str
    category: str
    description: str
    created_at: str
    updated_at: str
    version: int = 1


class VaultProvider(ABC):
    """Abstract base class for vault providers."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve a secret value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a secret value."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a secret."""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all secret keys."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a secret exists."""
        pass


class FileVaultProvider(VaultProvider):
    """
    File-based vault provider using JSON storage.
    
    This is a simple provider for development and single-user deployments.
    For production, consider using a dedicated secret management service.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the file vault provider.
        
        Args:
            storage_path: Path to the storage directory. Defaults to ~/.open_grace/secrets/
        """
        self.storage_path = Path(storage_path or os.path.expanduser("~/.open_grace/secrets"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.storage_path / "metadata.json"
        self._metadata: Dict[str, SecretMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from disk."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r') as f:
                    data = json.load(f)
                    for key, meta in data.items():
                        self._metadata[key] = SecretMetadata(**meta)
            except Exception:
                self._metadata = {}
    
    def _save_metadata(self):
        """Save metadata to disk."""
        data = {k: {
            "key": v.key,
            "category": v.category,
            "description": v.description,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
            "version": v.version
        } for k, v in self._metadata.items()}
        
        with open(self._metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_secret_path(self, key: str) -> Path:
        """Get the file path for a secret."""
        # Sanitize key for filesystem
        safe_key = key.replace('/', '_').replace('\\', '_')
        return self.storage_path / f"{safe_key}.secret"
    
    def get(self, key: str) -> Optional[str]:
        """Retrieve a secret value."""
        secret_path = self._get_secret_path(key)
        if not secret_path.exists():
            return None
        
        try:
            with open(secret_path, 'r') as f:
                return f.read()
        except Exception:
            return None
    
    def set(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a secret value."""
        secret_path = self._get_secret_path(key)
        
        # Write secret
        with open(secret_path, 'w') as f:
            f.write(value)
        
        # Set restrictive permissions
        os.chmod(secret_path, 0o600)
        
        # Update metadata
        now = datetime.now().isoformat()
        if key in self._metadata:
            meta = self._metadata[key]
            meta.updated_at = now
            meta.version += 1
            if metadata:
                meta.category = metadata.get('category', meta.category)
                meta.description = metadata.get('description', meta.description)
        else:
            self._metadata[key] = SecretMetadata(
                key=key,
                category=metadata.get('category', 'general') if metadata else 'general',
                description=metadata.get('description', '') if metadata else '',
                created_at=now,
                updated_at=now,
                version=1
            )
        
        self._save_metadata()
    
    def delete(self, key: str) -> bool:
        """Delete a secret."""
        secret_path = self._get_secret_path(key)
        
        if secret_path.exists():
            secret_path.unlink()
            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()
            return True
        
        return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all secret keys."""
        keys = []
        for secret_file in self.storage_path.glob("*.secret"):
            key = secret_file.stem.replace('_', '/')
            if prefix is None or key.startswith(prefix):
                keys.append(key)
        return keys
    
    def exists(self, key: str) -> bool:
        """Check if a secret exists."""
        return self._get_secret_path(key).exists()
    
    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret."""
        return self._metadata.get(key)
    
    def list_by_category(self, category: str) -> List[str]:
        """List secrets by category."""
        return [k for k, v in self._metadata.items() if v.category == category]
"""
Settings - Configuration management for Open Grace.

Loads configuration from environment variables and config files.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class GraceSettings:
    """Open Grace configuration settings."""
    
    # Instance settings
    instance_id: str = "open-grace-001"
    environment: str = "development"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_expiry_hours: int = 24
    
    # Model router settings
    default_routing_strategy: str = "hybrid"
    ollama_url: str = "http://localhost:11434"
    
    # Memory settings
    vector_store_backend: str = "faiss"
    vector_store_path: str = "~/.open_grace/vectors"
    
    # Vault settings
    vault_path: str = "~/.open_grace/vault.enc"
    
    @classmethod
    def from_env(cls) -> "GraceSettings":
        """Load settings from environment variables."""
        return cls(
            instance_id=os.getenv("OPEN_GRACE_INSTANCE_ID", "open-grace-001"),
            environment=os.getenv("OPEN_GRACE_ENV", "development"),
            api_host=os.getenv("OPEN_GRACE_API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("OPEN_GRACE_API_PORT", "8000")),
            secret_key=os.getenv("OPEN_GRACE_SECRET_KEY", "dev-secret-key-change-in-production"),
            jwt_expiry_hours=int(os.getenv("OPEN_GRACE_JWT_EXPIRY", "24")),
            default_routing_strategy=os.getenv("OPEN_GRACE_ROUTING_STRATEGY", "hybrid"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            vector_store_backend=os.getenv("OPEN_GRACE_VECTOR_BACKEND", "faiss"),
            vector_store_path=os.getenv("OPEN_GRACE_VECTOR_PATH", "~/.open_grace/vectors"),
            vault_path=os.getenv("OPEN_GRACE_VAULT_PATH", "~/.open_grace/vault.enc"),
        )


# Global settings instance
_settings: Optional[GraceSettings] = None


def get_settings() -> GraceSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = GraceSettings.from_env()
    return _settings
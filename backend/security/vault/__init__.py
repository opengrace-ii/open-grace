"""
Secret Vault - Secure credential management for Open Grace.

The Secret Vault ensures that sensitive information like API keys,
passwords, and tokens are never exposed to LLMs or logged.
"""

from open_grace.security.vault.vault import SecretVault, get_vault
from open_grace.security.vault.providers import VaultProvider, FileVaultProvider

__all__ = [
    "SecretVault",
    "get_vault",
    "VaultProvider",
    "FileVaultProvider",
]
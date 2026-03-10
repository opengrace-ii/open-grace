"""
Authentication - API key and JWT authentication for Open Grace.

Provides:
- API key management
- JWT token generation and validation
- User management
- Session tracking
"""

import os
import uuid
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from open_grace.observability.logger import get_logger


class TokenType(Enum):
    """Types of authentication tokens."""
    API_KEY = "api_key"
    JWT_ACCESS = "jwt_access"
    JWT_REFRESH = "jwt_refresh"


@dataclass
class User:
    """User account."""
    id: str
    username: str
    email: str
    created_at: str
    is_active: bool = True
    is_admin: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIKey:
    """API key for authentication."""
    key_id: str
    key_hash: str
    name: str
    user_id: str
    created_at: str
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    token: str
    created_at: str
    expires_at: str
    last_activity: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'last_activity': self.last_activity,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_name': self.device_name or 'Unknown Device'
        }


class AuthManager:
    """
    Manages authentication for Open Grace.
    
    Features:
    - API key generation and validation
    - JWT token lifecycle
    - User management
    - Session tracking
    - Permission-based access
    
    Usage:
        auth = AuthManager()
        
        # Create API key
        api_key, key_id = auth.create_api_key(user_id="user123", name="My App")
        
        # Validate API key
        user = auth.validate_api_key(api_key)
        
        # Create JWT token
        token = auth.create_jwt_token(user_id="user123")
        
        # Validate JWT
        payload = auth.validate_jwt_token(token)
    """
    
    def __init__(self, 
                 secret_key: Optional[str] = None,
                 jwt_algorithm: str = "HS256",
                 jwt_expiry_hours: int = 24):
        """
        Initialize the auth manager.
        
        Args:
            secret_key: Secret key for signing (auto-generated if not provided)
            jwt_algorithm: JWT signing algorithm
            jwt_expiry_hours: JWT token expiry time
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiry_hours = jwt_expiry_hours
        self.logger = get_logger()
        
        # Storage (in production, use database)
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self._api_key_hashes: Dict[str, str] = {}  # key_hash -> key_id
        self._sessions: Dict[str, Session] = {}
        
        if not JWT_AVAILABLE:
            self.logger.warning("PyJWT not available. JWT authentication disabled.")
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if no users exist."""
        if not self._users:
            admin = self.create_user(
                username="admin",
                email="admin@opengrace.local",
                is_admin=True
            )
            self.logger.info(f"Default admin user created: {admin.username}")
            
            # Also create a regular user for testing
            user = self.create_user(
                username="opengrace",
                email="user@opengrace.local",
                is_admin=False
            )
            self.logger.info(f"Default user created: {user.username}")
    
    # User Management
    
    def create_user(self, username: str, email: str,
                   is_admin: bool = False,
                   metadata: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email
            is_admin: Whether user has admin privileges
            metadata: Additional user metadata
            
        Returns:
            Created User
        """
        user_id = str(uuid.uuid4())
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            created_at=datetime.now().isoformat(),
            is_active=True,
            is_admin=is_admin,
            metadata=metadata or {}
        )
        
        self._users[user_id] = user
        self.logger.info(f"User created: {username} ({user_id})")
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def list_users(self) -> List[User]:
        """List all users."""
        return list(self._users.values())
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._users:
            del self._users[user_id]
            
            # Clean up associated API keys
            keys_to_delete = [
                key_id for key_id, key in self._api_keys.items()
                if key.user_id == user_id
            ]
            for key_id in keys_to_delete:
                self.revoke_api_key(key_id)
            
            return True
        return False
    
    # API Key Management
    
    def create_api_key(self, user_id: str, name: str,
                      expires_days: Optional[int] = None,
                      permissions: Optional[List[str]] = None) -> tuple[str, str]:
        """
        Create a new API key.
        
        Args:
            user_id: User ID
            name: Key name/description
            expires_days: Days until expiry (None for no expiry)
            permissions: List of permissions for this key
            
        Returns:
            Tuple of (api_key, key_id)
        """
        # Generate key
        api_key = f"og_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_id = str(uuid.uuid4())
        
        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        # Store key info
        key_info = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            is_active=True,
            permissions=permissions or []
        )
        
        self._api_keys[key_id] = key_info
        self._api_key_hashes[key_hash] = key_id
        
        self.logger.info(f"API key created: {key_id} for user {user_id}")
        
        return api_key, key_id
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        Validate an API key and return the associated user.
        
        Args:
            api_key: API key to validate
            
        Returns:
            User if valid, None otherwise
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_id = self._api_key_hashes.get(key_hash)
        
        if not key_id:
            return None
        
        key_info = self._api_keys.get(key_id)
        if not key_info or not key_info.is_active:
            return None
        
        # Check expiry
        if key_info.expires_at:
            expires = datetime.fromisoformat(key_info.expires_at)
            if datetime.now() > expires:
                return None
        
        # Update last used
        key_info.last_used_at = datetime.now().isoformat()
        
        return self._users.get(key_info.user_id)
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        key_info = self._api_keys.get(key_id)
        if not key_info:
            return False
        
        key_info.is_active = False
        
        # Remove from hash lookup
        if key_info.key_hash in self._api_key_hashes:
            del self._api_key_hashes[key_info.key_hash]
        
        self.logger.info(f"API key revoked: {key_id}")
        return True
    
    def list_api_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """List API keys, optionally filtered by user."""
        keys = list(self._api_keys.values())
        if user_id:
            keys = [k for k in keys if k.user_id == user_id]
        return keys
    
    # JWT Token Management
    
    def create_jwt_token(self, user_id: str,
                        expires_hours: Optional[int] = None,
                        additional_claims: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a JWT access token.
        
        Args:
            user_id: User ID
            expires_hours: Token expiry in hours
            additional_claims: Additional JWT claims
            
        Returns:
            JWT token string
        """
        if not JWT_AVAILABLE:
            self.logger.error("PyJWT not available")
            return None
        
        expires = expires_hours or self.jwt_expiry_hours
        expiry = datetime.utcnow() + timedelta(hours=expires)
        
        payload = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": expiry,
            "type": TokenType.JWT_ACCESS.value,
            "jti": str(uuid.uuid4())
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
        
        # Extract device info from claims
        device_name = additional_claims.get('device_name', 'Unknown') if additional_claims else 'Unknown'
        ip_address = additional_claims.get('ip_address', 'Unknown') if additional_claims else 'Unknown'
        
        # Create session
        session = Session(
            session_id=payload["jti"],
            user_id=user_id,
            token=token,
            created_at=datetime.now().isoformat(),
            expires_at=expiry.isoformat(),
            last_activity=datetime.now().isoformat(),
            device_name=device_name,
            ip_address=ip_address
        )
        self._sessions[session.session_id] = session
        
        return token
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload if valid, None otherwise
        """
        if not JWT_AVAILABLE:
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            
            # Check if session exists and is valid
            session_id = payload.get("jti")
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_activity = datetime.now().isoformat()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def revoke_jwt_token(self, token: str) -> bool:
        """Revoke a JWT token."""
        payload = self.validate_jwt_token(token)
        if not payload:
            return False
        
        session_id = payload.get("jti")
        if session_id and session_id in self._sessions:
            del self._sessions[session_id]
            return True
        
        return False
    
    def get_user_from_token(self, token: str, token_type: TokenType = TokenType.JWT_ACCESS) -> Optional[User]:
        """
        Get user from token.
        
        Args:
            token: Token string
            token_type: Type of token
            
        Returns:
            User if valid, None otherwise
        """
        if token_type == TokenType.API_KEY:
            return self.validate_api_key(token)
        elif token_type == TokenType.JWT_ACCESS:
            payload = self.validate_jwt_token(token)
            if payload:
                return self._users.get(payload.get("sub"))
        
        return None
    
    # Session Management
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """List active sessions."""
        sessions = list(self._sessions.values())
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sessions
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if datetime.fromisoformat(session.expires_at) < now
        ]
        for sid in expired:
            del self._sessions[sid]
    
    def terminate_all_user_sessions(self, user_id: str) -> int:
        """
        Terminate all sessions for a user.
        
        Args:
            user_id: User ID to terminate sessions for
            
        Returns:
            Number of sessions terminated
        """
        sessions_to_remove = [
            sid for sid, session in self._sessions.items()
            if session.user_id == user_id
        ]
        for sid in sessions_to_remove:
            del self._sessions[sid]
        
        self.logger.info(f"Terminated {len(sessions_to_remove)} sessions for user {user_id}")
        return len(sessions_to_remove)
    
    def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active sessions with user info.
        
        Returns:
            List of session dictionaries with user details
        """
        self.cleanup_expired_sessions()
        result = []
        for session in self._sessions.values():
            user = self._users.get(session.user_id)
            session_data = session.to_dict()
            session_data['username'] = user.username if user else 'Unknown'
            session_data['is_admin'] = user.is_admin if user else False
            result.append(session_data)
        return result
    
    # Utility
    
    def get_auth_summary(self, user_id: str) -> Dict[str, Any]:
        """Get authentication summary for a user."""
        return {
            "user_id": user_id,
            "api_keys": len([k for k in self._api_keys.values() if k.user_id == user_id]),
            "active_sessions": len([s for s in self._sessions.values() if s.user_id == user_id]),
            "jwt_available": JWT_AVAILABLE
        }


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def set_auth_manager(manager: AuthManager):
    """Set the global auth manager instance."""
    global _auth_manager
    _auth_manager = manager
from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional, List
from backend.api.models import LoginRequest, LoginResponse, APIKeyResponse, CreateAPIKeyRequest
from backend.api.deps import get_auth_manager, security
from backend.security.auth import User, AuthManager
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])

async def _get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current user from token."""
    if not credentials:
        return None
    
    auth_manager = get_auth_manager()
    token = credentials.credentials
    
    # Try JWT first
    user = auth_manager.get_user_from_token(token)
    if user:
        return user
    
    # Try API key
    user = auth_manager.validate_api_key(token)
    return user

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, request_obj: Request):
    """Login and get access token."""
    auth_manager = get_auth_manager()
    
    # Find user by username
    user = auth_manager.get_user_by_username(request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get device info from headers
    user_agent = request_obj.headers.get('user-agent', 'Unknown')
    client_ip = request_obj.client.host if request_obj.client else 'Unknown'
    
    # Create JWT token with device info
    token = auth_manager.create_jwt_token(
        user_id=user.id,
        additional_claims={
            'device_name': user_agent[:50] if user_agent else 'Unknown',
            'ip_address': client_ip
        }
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create token"
        )
    
    return LoginResponse(
        access_token=token,
        expires_in=86400  # 24 hours
    )

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(_get_current_user)
):
    """Create a new API key."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    
    api_key, key_id = auth_manager.create_api_key(
        user_id=current_user.id,
        name=request.name,
        expires_days=request.expires_days
    )
    
    key_info = auth_manager._api_keys.get(key_id)
    
    return APIKeyResponse(
        key_id=key_id,
        api_key=api_key,
        name=request.name,
        created_at=key_info.created_at,
        expires_at=key_info.expires_at
    )

@router.get("/api-keys")
async def list_api_keys(current_user: User = Depends(_get_current_user)):
    """List API keys for current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    keys = auth_manager.list_api_keys(user_id=current_user.id)
    return [
        {
            "key_id": k.key_id,
            "name": k.name,
            "created_at": k.created_at,
            "expires_at": k.expires_at,
            "last_used_at": k.last_used_at,
            "is_active": k.is_active
        }
        for k in keys
    ]

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(_get_current_user)
):
    """Revoke an API key."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    
    # Verify key belongs to user
    key_info = auth_manager._api_keys.get(key_id)
    if not key_info or key_info.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    auth_manager.revoke_api_key(key_id)
    return {"success": True, "message": "API key revoked"}

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(_get_current_user)):
    """Get current user information."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }

@router.get("/sessions")
async def get_active_sessions(current_user: User = Depends(_get_current_user)):
    """Get all active sessions (admin only)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    
    # Get user's own sessions
    user_sessions = auth_manager.list_sessions(current_user.id)
    
    # Admin can see all sessions
    all_sessions = []
    if current_user.is_admin:
        all_sessions = auth_manager.get_all_active_sessions()
    else:
        all_sessions = [s.to_dict() for s in user_sessions]
    
    return {
        "sessions": all_sessions,
        "total": len(all_sessions)
    }

@router.post("/sessions/terminate-all")
async def terminate_all_sessions(
    current_user: User = Depends(_get_current_user)
):
    """Terminate all sessions for current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    count = auth_manager.terminate_all_user_sessions(current_user.id)
    
    return {
        "success": True,
        "message": f"Terminated {count} sessions",
        "terminated_count": count
    }

@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: User = Depends(_get_current_user)
):
    """Terminate a specific session."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_manager = get_auth_manager()
    
    # Get session to check ownership
    sessions = auth_manager.list_sessions()
    session = None
    for s in sessions:
        if s.session_id == session_id:
            session = s
            break
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Only admin or session owner can terminate
    if not current_user.is_admin and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot terminate this session"
        )
    
    success = auth_manager.revoke_session(session_id)
    
    return {
        "success": success,
        "message": "Session terminated" if success else "Failed to terminate session"
    }

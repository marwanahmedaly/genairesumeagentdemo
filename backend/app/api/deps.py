"""
Dependencies
Dependency injection for FastAPI routes
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.security import decode_token
from ..core.logger import get_logger
from ..core.exceptions import AuthenticationError
from ..models.database import get_supabase_client
from ..services.storage_service import StorageService

logger = get_logger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Dictionary containing user_id and email
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = await decode_token(token)
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject claim"
            )
        
        email = payload.get("email", "").lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email claim"
            )
        
        logger.debug(f"User authenticated: {user_id}")
        return {"id": user_id, "email": email}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_supabase_client():
    """
    Dependency to get Supabase client
    
    Returns:
        Supabase client instance
    """
    return get_supabase_client()


def get_storage_service() -> StorageService:
    """
    Dependency to get storage service
    
    Returns:
        StorageService instance
    """
    return StorageService()
"""
Security Module
JWT validation, token management, and authentication utilities
"""

import httpx
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
from .config import settings


# Global cache for JWKS
_cached_jwks: Optional[Dict[str, Any]] = None


async def get_jwks() -> Dict[str, Any]:
    """
    Fetch and cache JWKS (JSON Web Key Set) from Supabase
    
    Returns:
        Dict containing JWKS for JWT validation
    """
    global _cached_jwks
    
    if _cached_jwks is None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.jwks_url)
                response.raise_for_status()
                _cached_jwks = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch JWKS: {str(e)}"
            )
    
    return _cached_jwks


def clear_jwks_cache() -> None:
    """Clear the cached JWKS (useful for testing or token refresh)"""
    global _cached_jwks
    _cached_jwks = None


async def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        jwks = await get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=settings.jwt_algorithms,
            audience=settings.jwt_audience,
            options={"verify_aud": False}
        )
        return payload
    except JWTError as e:
        # Clear cache on error to force refresh
        clear_jwks_cache()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing user_id and email
    """
    payload = decode_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim"
        )
    
    email = payload.get("email", "").lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email claim"
        )
    
    return {
        "id": user_id,
        "email": email
    }


def verify_ownership(user_id: str, resource_key: str) -> bool:
    """
    Verify that a user owns a resource based on UUID prefix
    
    Args:
        user_id: User's UUID
        resource_key: Resource key (e.g., R2 key)
        
    Returns:
        True if user owns the resource, False otherwise
    """
    return resource_key.startswith(user_id)
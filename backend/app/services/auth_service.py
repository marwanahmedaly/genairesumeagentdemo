"""
Authentication Service
Business logic for authentication operations
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from ..core.security import decode_token, get_user_from_token, verify_ownership
from ..core.logger import get_logger
from ..core.exceptions import AuthenticationError, AuthorizationError

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication and authorization operations
    """
    
    @staticmethod
    async def validate_token(token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            logger.debug("Validating JWT token")
            payload = await decode_token(token)
            logger.info(f"Token validated for user: {payload.get('sub')}")
            return payload
        except HTTPException as e:
            logger.warning(f"Token validation failed: {e.detail}")
            raise AuthenticationError(message=e.detail)
    
    @staticmethod
    async def get_current_user(token: str) -> Dict[str, Any]:
        """
        Get current user from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing user_id and email
            
        Raises:
            AuthenticationError: If token is invalid or missing claims
        """
        try:
            logger.debug("Extracting user from token")
            user = get_user_from_token(token)
            logger.info(f"User authenticated: {user['id']}")
            return user
        except HTTPException as e:
            logger.warning(f"User extraction failed: {e.detail}")
            raise AuthenticationError(message=e.detail)
    
    @staticmethod
    def verify_resource_ownership(user_id: str, resource_key: str) -> bool:
        """
        Verify that a user owns a resource
        
        Args:
            user_id: User's UUID
            resource_key: Resource key (e.g., R2 key)
            
        Returns:
            True if user owns the resource
            
        Raises:
            AuthorizationError: If user doesn't own the resource
        """
        if not verify_ownership(user_id, resource_key):
            logger.warning(
                f"Ownership verification failed: user {user_id} does not own resource {resource_key}"
            )
            raise AuthorizationError(
                message="Access denied: You do not have permission to access this resource",
                details={"user_id": user_id, "resource_key": resource_key}
            )
        
        logger.debug(f"Ownership verified: user {user_id} owns resource {resource_key}")
        return True
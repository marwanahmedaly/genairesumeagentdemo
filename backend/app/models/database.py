"""
Database Module
Supabase client initialization and database connection management
"""

from supabase import create_client, Client
from ..core.config import settings
from ..core.logger import get_logger

logger = get_logger(__name__)


# Global Supabase client instance
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If Supabase URL or key is not configured
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError(
                "Supabase URL and key must be configured in environment variables"
            )
        
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    return _supabase_client


def reset_supabase_client() -> None:
    """
    Reset Supabase client (useful for testing)
    """
    global _supabase_client
    _supabase_client = None
    logger.info("Supabase client reset")
"""
Base Repository
Abstract base class for all repositories
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from ..models.database import get_supabase_client
from ..core.logger import get_logger
from ..core.exceptions import DatabaseError

logger = get_logger(__name__)


class BaseRepository(ABC):
    """
    Abstract base class for all repositories
    
    Provides common functionality and enforces interface
    """
    
    def __init__(self):
        """Initialize repository with Supabase client"""
        self._client = get_supabase_client()
        self._table_name: str = ""
    
    @property
    def table_name(self) -> str:
        """Get the table name for this repository"""
        if not self._table_name:
            raise ValueError("Table name not set in repository")
        return self._table_name
    
    def _handle_error(self, operation: str, error: Exception) -> None:
        """
        Handle database errors consistently
        
        Args:
            operation: Description of the operation that failed
            error: The exception that occurred
            
        Raises:
            DatabaseError: Wrapped exception with context
        """
        error_msg = f"Failed to {operation} in table '{self.table_name}': {str(error)}"
        logger.error(error_msg)
        raise DatabaseError(message=error_msg, details={"operation": operation, "original_error": str(error)})
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record
        
        Args:
            data: Dictionary of field names and values
            
        Returns:
            Created record
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            logger.debug(f"Creating record in {self.table_name}: {data}")
            response = self._client.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            self._handle_error("create record", e)
    
    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID
        
        Args:
            record_id: The record ID
            
        Returns:
            Record dictionary or None if not found
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Fetching record {record_id} from {self.table_name}")
            response = self._client.table(self.table_name).select("*").eq("id", record_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_error(f"get record by ID {record_id}", e)
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all records, optionally filtered
        
        Args:
            filters: Optional dictionary of field filters
            
        Returns:
            List of record dictionaries
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Fetching records from {self.table_name} with filters: {filters}")
            query = self._client.table(self.table_name).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            self._handle_error("get records", e)
    
    def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record
        
        Args:
            record_id: The record ID
            data: Dictionary of field names and values to update
            
        Returns:
            Updated record
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            logger.debug(f"Updating record {record_id} in {self.table_name}: {data}")
            response = self._client.table(self.table_name).update(data).eq("id", record_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            self._handle_error(f"update record {record_id}", e)
    
    def delete(self, record_id: str) -> bool:
        """
        Delete a record
        
        Args:
            record_id: The record ID
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            logger.debug(f"Deleting record {record_id} from {self.table_name}")
            response = self._client.table(self.table_name).delete().eq("id", record_id).execute()
            return len(response.data) > 0
        except Exception as e:
            self._handle_error(f"delete record {record_id}", e)
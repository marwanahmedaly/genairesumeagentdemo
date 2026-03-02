"""
Resume Repository
Data access layer for resume history operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseRepository
from ..models.schemas import HistoryRecord
from ..core.logger import get_logger
from ..core.exceptions import ResourceNotFoundError


def parse_datetime(date_string: str) -> datetime:
    """
    Parse datetime string from database, handling various ISO 8601 formats.

    This function handles:
    - Standard ISO 8601 with microseconds: 2023-01-01T12:00:00.123456+00:00
    - ISO 8601 without microseconds: 2023-01-01T12:00:00+00:00
    - ISO 8601 with Z timezone: 2023-01-01T12:00:00.123456Z

    Args:
        date_string: ISO 8601 datetime string from database

    Returns:
        Parsed datetime object
    """
    try:
        # Try standard fromisoformat first (Python 3.7+)
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError:
        # Fallback for older Python versions or malformed strings
        # Remove timezone info and parse with strptime
        # Handle formats like: 2023-01-01T12:00:00.123456+00:00
        if '+' in date_string:
            date_part, tz_part = date_string.split('+', 1)
            tz_part = '+' + tz_part
        elif date_string.endswith('Z'):
            date_part = date_string[:-1]
            tz_part = '+00:00'
        else:
            date_part = date_string
            tz_part = '+00:00'

        # Ensure microseconds are properly formatted (6 digits)
        if '.' in date_part:
            time_part, micro_part = date_part.split('.', 1)
            # Pad or truncate microseconds to 6 digits
            micro_part = micro_part[:6].ljust(6, '0')
            date_part = f"{time_part}.{micro_part}"

        # Parse with strptime
        dt = datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S.%f')

        # Handle timezone if present
        if tz_part != '+00:00':
            # For simplicity, we'll assume UTC for now
            # In production, you might want to handle timezones properly
            pass

        return dt

logger = get_logger(__name__)


class ResumeRepository(BaseRepository):
    """
    Repository for resume history operations
    
    Handles CRUD operations for resume_history table
    """
    
    def __init__(self):
        """Initialize resume repository"""
        super().__init__()
        self._table_name = "resume_history"
    
    def save_resume_record(
        self,
        user_id: str,
        job_url: str,
        role_title: str,
        r2_key: str,
        match_score: int
    ) -> Dict[str, Any]:
        """
        Save a new resume alignment record
        
        Args:
            user_id: User's UUID
            job_url: Job posting URL
            role_title: Job role title
            r2_key: R2 storage key for PDF
            match_score: Match score (0-100)
            
        Returns:
            Created record dictionary
            
        Raises:
            DatabaseError: If save operation fails
        """
        data = {
            "user_id": user_id,
            "job_url": job_url,
            "role_title": role_title,
            "r2_key": r2_key,
            "match_score": match_score
        }
        
        logger.info(f"Saving resume record for user {user_id}")
        return self.create(data)
    
    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all resume records for a user, ordered by creation date (newest first)
        
        Args:
            user_id: User's UUID
            
        Returns:
            List of resume record dictionaries
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Fetching resume history for user {user_id}")
            response = (
                self._client
                .table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            self._handle_error(f"get user history for {user_id}", e)
    
    def get_resume_by_id(self, record_id: str) -> Dict[str, Any]:
        """
        Get a specific resume record by ID
        
        Args:
            record_id: Record UUID
            
        Returns:
            Resume record dictionary
            
        Raises:
            ResourceNotFoundError: If record not found
            DatabaseError: If query fails
        """
        record = self.get_by_id(record_id)
        
        if not record:
            logger.warning(f"Resume record {record_id} not found")
            raise ResourceNotFoundError(resource_type="Resume Record", resource_id=record_id)
        
        return record
    
    def get_resume_by_r2_key(self, r2_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a resume record by R2 storage key
        
        Args:
            r2_key: R2 storage key
            
        Returns:
            Resume record dictionary or None if not found
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Fetching resume record by R2 key: {r2_key}")
            response = (
                self._client
                .table(self.table_name)
                .select("*")
                .eq("r2_key", r2_key)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_error(f"get resume by R2 key {r2_key}", e)
    
    def delete_user_resume(self, user_id: str, record_id: str) -> bool:
        """
        Delete a resume record (with ownership check)
        
        Args:
            user_id: User's UUID (for ownership verification)
            record_id: Record UUID to delete
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            logger.info(f"Deleting resume record {record_id} for user {user_id}")
            response = (
                self._client
                .table(self.table_name)
                .delete()
                .eq("id", record_id)
                .eq("user_id", user_id)  # Ownership check
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            self._handle_error(f"delete resume record {record_id}", e)
    
    def to_history_record(self, data: Dict[str, Any]) -> HistoryRecord:
        """
        Convert dictionary to HistoryRecord schema

        Args:
            data: Dictionary from database

        Returns:
            HistoryRecord instance
        """
        return HistoryRecord(
            id=data.get("id", ""),
            user_id=data.get("user_id", ""),
            job_url=data.get("job_url", ""),
            role_title=data.get("role_title", ""),
            r2_key=data.get("r2_key", ""),
            match_score=data.get("match_score", 0),
            created_at=parse_datetime(data.get("created_at", datetime.utcnow().isoformat()))
        )

    # ============================================================================
    # Resume Preferences Methods
    # ============================================================================

    def create_preference(
        self,
        user_id: str,
        name: str,
        preferences: Dict[str, Any],
        is_default: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new resume preference profile

        Args:
            user_id: User's UUID
            name: Preference profile name
            preferences: Preference settings as dict
            is_default: Whether this should be the default preference

        Returns:
            Created preference record

        Raises:
            DatabaseError: If creation fails
        """
        try:
            logger.info(f"Creating preference '{name}' for user {user_id}")

            # Check if this is the user's first preference
            # If so, automatically set it as default
            existing_count = self._count_user_preferences(user_id)
            if existing_count == 0:
                is_default = True
                logger.info(f"First preference for user {user_id}, setting as default")

            # If setting as default, clear other defaults for this user
            if is_default:
                self._clear_default_preferences(user_id)

            data = {
                "user_id": user_id,
                "name": name,
                "preferences": preferences,
                "is_default": is_default
            }

            response = (
                self._client
                .table("resume_preferences")
                .insert(data)
                .execute()
            )

            if not response.data:
                raise Exception("No data returned from preference creation")

            return response.data[0]

        except Exception as e:
            self._handle_error(f"create preference for user {user_id}", e)

    def _count_user_preferences(self, user_id: str) -> int:
        """Count the number of preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of user's preferences
        """
        try:
            response = (
                self._client
                .table("resume_preferences")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            return response.count if response.count is not None else 0
        except Exception as e:
            logger.error(f"Failed to count preferences: {str(e)}")
            return 0

    def update_preference(
        self,
        user_id: str,
        preference_id: str,
        name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        is_default: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing preference profile

        Args:
            user_id: User's UUID (for ownership check)
            preference_id: Preference ID to update
            name: New name (optional)
            preferences: New preferences dict (optional)
            is_default: New default status (optional)

        Returns:
            Updated preference record

        Raises:
            ResourceNotFoundError: If preference not found or not owned by user
            DatabaseError: If update fails
        """
        try:
            logger.info(f"Updating preference {preference_id} for user {user_id}")

            # Check ownership
            existing = self.get_preference(user_id, preference_id)
            if not existing:
                raise ResourceNotFoundError(resource_type="Preference", resource_id=preference_id)

            # If setting as default, clear other defaults
            if is_default:
                self._clear_default_preferences(user_id)

            update_data = {}
            if name is not None:
                update_data["name"] = name
            if preferences is not None:
                update_data["preferences"] = preferences
            if is_default is not None:
                update_data["is_default"] = is_default

            update_data["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self._client
                .table("resume_preferences")
                .update(update_data)
                .eq("id", preference_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                raise ResourceNotFoundError(resource_type="Preference", resource_id=preference_id)

            return response.data[0]

        except ResourceNotFoundError:
            raise
        except Exception as e:
            self._handle_error(f"update preference {preference_id}", e)

    def delete_preference(self, user_id: str, preference_id: str) -> bool:
        """
        Delete a preference profile

        Args:
            user_id: User's UUID (for ownership check)
            preference_id: Preference ID to delete

        Returns:
            True if deleted successfully

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            logger.info(f"Deleting preference {preference_id} for user {user_id}")

            # Check if this is the default preference
            preference_to_delete = self.get_preference(user_id, preference_id)
            was_default = preference_to_delete and preference_to_delete.get("is_default", False)

            # Delete the preference
            response = (
                self._client
                .table("resume_preferences")
                .delete()
                .eq("id", preference_id)
                .eq("user_id", user_id)
                .execute()
            )

            # If we deleted the default preference, promote another one
            if was_default and len(response.data) > 0:
                self._promote_new_default_preference(user_id)

            return len(response.data) > 0

        except Exception as e:
            self._handle_error(f"delete preference {preference_id}", e)

    def list_preferences_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all preferences for a user

        Args:
            user_id: User's UUID

        Returns:
            List of preference records

        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Listing preferences for user {user_id}")

            response = (
                self._client
                .table("resume_preferences")
                .select("*")
                .eq("user_id", user_id)
                .order("is_default", desc=True)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data

        except Exception as e:
            self._handle_error(f"list preferences for user {user_id}", e)

    def get_preference(self, user_id: str, preference_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific preference by ID (with ownership check)

        Args:
            user_id: User's UUID
            preference_id: Preference ID

        Returns:
            Preference record or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug(f"Getting preference {preference_id} for user {user_id}")

            response = (
                self._client
                .table("resume_preferences")
                .select("*")
                .eq("id", preference_id)
                .eq("user_id", user_id)
                .execute()
            )

            return response.data[0] if response.data else None

        except Exception as e:
            self._handle_error(f"get preference {preference_id}", e)

    def set_default_preference(self, user_id: str, preference_id: str) -> bool:
        """
        Set a preference as the default for a user

        Args:
            user_id: User's UUID
            preference_id: Preference ID to set as default

        Returns:
            True if successfully set as default

        Raises:
            ResourceNotFoundError: If preference not found
            DatabaseError: If operation fails
        """
        try:
            logger.info(f"Setting preference {preference_id} as default for user {user_id}")

            # Check ownership
            existing = self.get_preference(user_id, preference_id)
            if not existing:
                raise ResourceNotFoundError(resource_type="Preference", resource_id=preference_id)

            # Clear other defaults and set this one
            self._clear_default_preferences(user_id)

            response = (
                self._client
                .table("resume_preferences")
                .update({"is_default": True, "updated_at": datetime.utcnow().isoformat()})
                .eq("id", preference_id)
                .eq("user_id", user_id)
                .execute()
            )

            return len(response.data) > 0

        except ResourceNotFoundError:
            raise
        except Exception as e:
            self._handle_error(f"set default preference {preference_id}", e)

    def _clear_default_preferences(self, user_id: str) -> None:
        """
        Clear default status from all preferences for a user

        Args:
            user_id: User's UUID

        Raises:
            DatabaseError: If operation fails
        """
        try:
            logger.debug(f"Clearing default preferences for user {user_id}")

            self._client.table("resume_preferences").update({
                "is_default": False,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("is_default", True).execute()

        except Exception as e:
            self._handle_error(f"clear default preferences for user {user_id}", e)

    def _promote_new_default_preference(self, user_id: str) -> None:
        """
        Promote the most recently created preference to default when the current default is deleted

        Args:
            user_id: User's UUID

        Raises:
            DatabaseError: If operation fails
        """
        try:
            logger.debug(f"Promoting new default preference for user {user_id}")

            # Find the most recently created preference for this user (excluding defaults)
            response = (
                self._client
                .table("resume_preferences")
                .select("id")
                .eq("user_id", user_id)
                .eq("is_default", False)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data:
                new_default_id = response.data[0]["id"]
                logger.info(f"Promoting preference {new_default_id} to default for user {user_id}")

                # Set the most recent preference as default
                self._client.table("resume_preferences").update({
                    "is_default": True,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", new_default_id).execute()
            else:
                logger.debug(f"No other preferences found for user {user_id} to promote to default")

        except Exception as e:
            self._handle_error(f"promote new default preference for user {user_id}", e)

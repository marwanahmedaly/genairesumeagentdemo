"""
History Routes
API endpoints for resume history
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..deps import get_current_user
from ...repositories.resume_repository import ResumeRepository
from ...services.resume_service import ResumeService
from ...models.schemas import HistoryRecord
from ...core.logger import get_logger
from ...core.exceptions import DatabaseError, ResourceNotFoundError

logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=List[HistoryRecord])
async def get_history(
    user: dict = Depends(get_current_user)
) -> List[HistoryRecord]:
    """
    Get user's resume history
    
    Returns all resume records for the authenticated user,
    ordered by creation date (newest first)
    
    Args:
        user: Current authenticated user
        
    Returns:
        List of history records
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info(f"Fetching history for user: {user['id']}")
        
        repo = ResumeRepository()
        records = repo.get_user_history(user['id'])
        
        # Convert to HistoryRecord schemas
        history_records = [
            repo.to_history_record(record) for record in records
        ]
        
        logger.info(f"Retrieved {len(history_records)} history records")
        return history_records
        
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history"
        )


@router.delete("/{record_id}")
async def delete_resume_record(
    record_id: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Delete a resume record and its associated PDF

    Deletes the resume record from the database and removes the PDF
    from storage. Includes ownership verification.

    Args:
        record_id: UUID of the resume record to delete
        user: Current authenticated user

    Returns:
        Dictionary with success message

    Raises:
        HTTPException: If record not found, ownership check fails, or deletion fails
    """
    try:
        logger.info(f"Deleting resume record {record_id} for user {user['id']}")

        # Attempt to delete the record and PDF
        deleted = ResumeService.delete_resume_record(user['id'], record_id)

        if not deleted:
            logger.warning(f"Failed to delete resume record {record_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume record not found or access denied"
            )

        logger.info(f"Successfully deleted resume record {record_id}")
        return {"message": "Resume record deleted successfully"}

    except ResourceNotFoundError as e:
        logger.error(f"Resource not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting record {record_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume record"
        )

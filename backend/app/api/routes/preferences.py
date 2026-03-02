"""
Preferences API Routes
Endpoints for managing user resume preference profiles
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..deps import get_current_user
from ...repositories.resume_repository import ResumeRepository
from ...models.schemas import (
    ResumePreference,
    CreatePreferenceRequest,
    UpdatePreferenceRequest,
    PreferencesResponse
)
from ...core.logger import get_logger
from ...core.exceptions import ResourceNotFoundError, DatabaseError

logger = get_logger(__name__)

router = APIRouter(tags=["Preferences"])


@router.get("/user/preferences", response_model=PreferencesResponse)
async def get_user_preferences(
    user: dict = Depends(get_current_user)
) -> PreferencesResponse:
    """
    Get all resume preferences for the current user

    Returns:
        List of user's preference profiles
    """
    user_id = user['id']

    try:
        logger.info(f"Getting preferences for user {user_id}")

        repo = ResumeRepository()
        preferences_data = repo.list_preferences_by_user(user_id)

        # Convert to schema objects
        preferences = []
        for pref_data in preferences_data:
            try:
                preference = ResumePreference(**pref_data)
                preferences.append(preference)
            except Exception as e:
                logger.warning(f"Failed to parse preference {pref_data.get('id')}: {e}")
                continue

        return PreferencesResponse(preferences=preferences)

    except DatabaseError as e:
        logger.error(f"Database error getting preferences: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/user/preferences", response_model=ResumePreference)
async def create_preference(
    request: CreatePreferenceRequest,
    user: dict = Depends(get_current_user)
) -> ResumePreference:
    """
    Create a new resume preference profile

    Args:
        request: Preference creation data

    Returns:
        Created preference profile
    """
    user_id = user['id']

    try:
        logger.info(f"Creating preference '{request.name}' for user {user_id}")

        repo = ResumeRepository()
        preference_data = repo.create_preference(
            user_id=user_id,
            name=request.name,
            preferences=request.preferences.model_dump(),
            is_default=request.is_default
        )

        return ResumePreference(**preference_data)

    except DatabaseError as e:
        logger.error(f"Database error creating preference: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preference"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.put("/user/preferences/{preference_id}", response_model=ResumePreference)
async def update_preference(
    preference_id: str,
    request: UpdatePreferenceRequest,
    user: dict = Depends(get_current_user)
) -> ResumePreference:
    """
    Update an existing preference profile

    Args:
        preference_id: ID of preference to update
        request: Update data

    Returns:
        Updated preference profile
    """
    user_id = user['id']

    try:
        logger.info(f"Updating preference {preference_id} for user {user_id}")

        repo = ResumeRepository()
        preference_data = repo.update_preference(
            user_id=user_id,
            preference_id=preference_id,
            name=request.name,
            preferences=request.preferences.model_dump() if request.preferences else None,
            is_default=request.is_default
        )

        return ResumePreference(**preference_data)

    except ResourceNotFoundError as e:
        logger.warning(f"Preference not found: {e.resource_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference {preference_id} not found"
        )
    except DatabaseError as e:
        logger.error(f"Database error updating preference: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preference"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/user/preferences/{preference_id}")
async def delete_preference(
    preference_id: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Delete a preference profile

    Args:
        preference_id: ID of preference to delete

    Returns:
        Success message
    """
    user_id = user['id']

    try:
        logger.info(f"Deleting preference {preference_id} for user {user_id}")

        repo = ResumeRepository()
        deleted = repo.delete_preference(user_id, preference_id)

        if not deleted:
            raise ResourceNotFoundError(resource_type="Preference", resource_id=preference_id)

        return {"message": "Preference deleted successfully"}

    except ResourceNotFoundError as e:
        logger.warning(f"Preference not found: {e.resource_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference {preference_id} not found"
        )
    except DatabaseError as e:
        logger.error(f"Database error deleting preference: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete preference"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/user/preferences/{preference_id}/default")
async def set_default_preference(
    preference_id: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Set a preference as the default for the user

    Args:
        preference_id: ID of preference to set as default

    Returns:
        Success message
    """
    user_id = user['id']

    try:
        logger.info(f"Setting preference {preference_id} as default for user {user_id}")

        repo = ResumeRepository()
        success = repo.set_default_preference(user_id, preference_id)

        if not success:
            raise ResourceNotFoundError(resource_type="Preference", resource_id=preference_id)

        return {"message": "Preference set as default successfully"}

    except ResourceNotFoundError as e:
        logger.warning(f"Preference not found: {e.resource_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference {preference_id} not found"
        )
    except DatabaseError as e:
        logger.error(f"Database error setting default preference: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default preference"
        )
    except Exception as e:
        logger.error(f"Unexpected error setting default preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
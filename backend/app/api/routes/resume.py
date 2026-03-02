"""
Resume Routes
API endpoints for resume alignment operations
"""

import os
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, Body
import json
from ..deps import get_current_user, get_storage_service
from ...services.resume_service import ResumeService
from ...repositories.resume_repository import ResumeRepository
from ...generators.pdf_generator import PDFGenerator
from ...models.schemas import FullAlignmentResponse, DownloadURLResponse, UserResumeOverrides
from ...core.logger import get_logger
from ...core.exceptions import (
    ScrapingError,
    ValidationError,
    AIServiceError,
    StorageError,
    PDFGenerationError
)

logger = get_logger(__name__)

router = APIRouter(tags=["Resume"])


@router.post("/full-alignment", response_model=FullAlignmentResponse)
async def full_alignment(
    url: str = Query(..., description="Job posting URL"),
    file: UploadFile = File(..., description="Resume PDF file"),
    overrides: str = Form(None, description="User overrides for resume tailoring (JSON string)"),
    preference_id: str = Form(None, description="User preference profile ID to use"),
    user: dict = Depends(get_current_user),
    storage_service = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Complete resume alignment workflow
    
    1. Scrape job description from URL
    2. Extract text from uploaded PDF
    3. Extract structured JD data using AI
    4. Align resume to JD using AI
    5. Generate optimized PDF
    6. Upload PDF to R2 storage
    7. Save record to database
    
    Args:
        url: Job posting URL
        file: Uploaded PDF resume file
        user: Current authenticated user
        storage_service: Storage service instance
        
    Returns:
        Dictionary containing alignment results and R2 key
        
    Raises:
        HTTPException: If any step fails
    """
    user_id = user['id']
    temp_path = None
    pdf_path = None
    
    try:
        logger.info(f"Starting full alignment for user {user_id}")
        
        # Step 1: Validate uploaded file
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted. Please upload a valid PDF file."
            )
        
        # Check MIME type
        if file.content_type not in ['application/pdf', 'application/x-pdf']:
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted. Please upload a valid PDF file."
            )
        
        # Read file content and check size (10MB limit)
        content = await file.read()
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit. Please upload a smaller PDF file."
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty. Please upload a valid PDF file."
            )
        
        # Step 2: Save uploaded file temporarily
        temp_path = f"temp_{user_id}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Step 2: Process resume alignment
        overrides_dict = None

        # Load preference if provided
        if preference_id:
            try:
                repo = ResumeRepository()
                preference_data = repo.get_preference(user_id, preference_id)
                if preference_data:
                    overrides_dict = preference_data.get('preferences', {})
                    logger.info(f"Loaded preference '{preference_data.get('name')}' for user {user_id}")
                else:
                    logger.warning(f"Preference {preference_id} not found for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to load preference {preference_id}: {str(e)}")

        # Apply explicit overrides if provided (takes precedence over preference)
        if overrides:
            try:
                explicit_overrides = json.loads(overrides)
                if overrides_dict:
                    # Merge explicit overrides with preference (explicit takes precedence)
                    overrides_dict = {**overrides_dict, **explicit_overrides}
                else:
                    overrides_dict = explicit_overrides
                logger.info("Applied explicit overrides")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in overrides: {overrides}")

        alignment_result = await ResumeService.process_resume_alignment(url, temp_path, overrides_dict)

        # Extract role title from alignment result (added during processing)
        role_title = alignment_result.get('role_title', 'Unknown_Role')
        match_score = alignment_result.get('match_score', 0)

        # Step 3: Generate PDF
        generator = PDFGenerator()
        pdf_path = generator.create_pdf(alignment_result)

        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF generation failed"
            )

        # Step 4: Upload to R2 with meaningful filename
        timestamp = datetime.utcnow()
        r2_key = storage_service.upload_pdf(
            pdf_path,
            user_id,
            timestamp,
            role_title=role_title,
            match_score=match_score
        )

        # Step 5: Save to database
        repo = ResumeRepository()
        repo.save_resume_record(
            user_id=user_id,
            job_url=url,
            role_title=role_title,
            r2_key=r2_key,
            match_score=match_score
        )
        
        # Add R2 key to result
        alignment_result['r2_key'] = r2_key
        
        logger.info(f"Full alignment completed for user {user_id}")
        return alignment_result
        
    except ScrapingError as e:
        logger.error(f"Scraping error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AIServiceError as e:
        logger.error(f"AI service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message
        )
    except StorageError as e:
        logger.error(f"Storage error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message
        )
    except PDFGenerationError as e:
        logger.error(f"PDF generation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in full alignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
    finally:
        # Cleanup temporary files
        ResumeService.cleanup_temp_files(temp_path, pdf_path)


@router.get("/generate-download-url", response_model=DownloadURLResponse)
async def generate_download_url(
    r2_key: str = Query(..., description="R2 storage key"),
    user: dict = Depends(get_current_user),
    storage_service = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Generate presigned download URL for a PDF
    
    Args:
        r2_key: R2 storage key for the PDF
        user: Current authenticated user
        storage_service: Storage service instance
        
    Returns:
        Dictionary containing download URL and expiry time
        
    Raises:
        HTTPException: If user doesn't own the resource or URL generation fails
    """
    user_id = user['id']
    
    try:
        logger.info(f"Generating download URL for {r2_key}")
        
        # Verify ownership
        if not r2_key.startswith(user_id):
            logger.warning(f"Ownership check failed: user {user_id} does not own {r2_key}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this resource"
            )
        
        # Generate download URL
        download_url = storage_service.generate_download_url(r2_key)
        
        logger.info(f"Download URL generated for {r2_key}")
        return {
            "download_url": download_url,
            "expires_in": 3600  # 1 hour
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )
"""
Storage Service
Business logic for Cloudflare R2 storage operations
"""

import os
import re
import boto3
from botocore.config import Config
from typing import Optional
from datetime import datetime
from ..core.config import settings
from ..core.logger import get_logger
from ..core.exceptions import StorageError

logger = get_logger(__name__)


class StorageService:
    """
    Service for Cloudflare R2 storage operations
    Singleton pattern to ensure single client instance
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(StorageService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize storage service with S3 client (only once)"""
        if self._initialized:
            return

        self._client = None
        self._bucket_name = settings.r2_bucket_name
        self._initialized = True
    
    @property
    def client(self):
        """Lazy initialization of S3 client"""
        if self._client is None:
            try:
                self._client = boto3.client(
                    "s3",
                    endpoint_url=settings.r2_endpoint_url,
                    aws_access_key_id=settings.r2_access_key_id,
                    aws_secret_access_key=settings.r2_secret_access_key,
                    config=Config(signature_version="s3v4"),
                    region_name="auto"
                )
                logger.info("R2 storage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize R2 client: {str(e)}")
                raise StorageError(
                    message="Failed to initialize storage client",
                    details={"error": str(e)}
                )
        return self._client
    
    def upload_pdf(
        self,
        file_path: str,
        user_id: str,
        timestamp: Optional[datetime] = None,
        role_title: Optional[str] = None,
        match_score: Optional[int] = None
    ) -> str:
        """
        Upload PDF file to R2 storage
        
        Args:
            file_path: Local path to PDF file
            user_id: User's UUID (for folder structure)
            timestamp: Optional timestamp for filename
            
        Returns:
            R2 key (storage path)
            
        Raises:
            StorageError: If upload fails
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise StorageError(
                message="File not found",
                details={"file_path": file_path}
            )
        
        try:
            # Generate R2 key with user folder
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Create meaningful filename
            date_str = timestamp.strftime('%Y%m%d_%H%M%S')

            if role_title and match_score is not None:
                # Sanitize role title for filename
                sanitized_role = self._sanitize_filename(role_title)
                filename = f"{sanitized_role}_{match_score}_{date_str}.pdf"
            else:
                filename = f"{date_str}.pdf"

            r2_key = f"{user_id}/{filename}"
            
            logger.info(f"Uploading PDF to R2: {r2_key}")
            
            # Upload file
            with open(file_path, "rb") as f:
                self.client.upload_fileobj(
                    f,
                    self._bucket_name,
                    r2_key,
                    ExtraArgs={"ContentType": "application/pdf"}
                )
            
            logger.info(f"PDF uploaded successfully: {r2_key}")
            return r2_key
            
        except Exception as e:
            logger.error(f"Failed to upload PDF: {str(e)}")
            raise StorageError(
                message="Failed to upload PDF to storage",
                details={"file_path": file_path, "error": str(e)}
            )
    
    def generate_download_url(self, r2_key: str) -> str:
        """
        Generate presigned download URL for a PDF
        
        Args:
            r2_key: R2 storage key
            
        Returns:
            Presigned URL string
            
        Raises:
            StorageError: If URL generation fails
        """
        try:
            logger.debug(f"Generating download URL for: {r2_key}")
            
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self._bucket_name,
                    'Key': r2_key
                },
                ExpiresIn=settings.download_url_expiry
            )
            
            logger.info(f"Download URL generated for: {r2_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL: {str(e)}")
            raise StorageError(
                message="Failed to generate download URL",
                details={"r2_key": r2_key, "error": str(e)}
            )
    
    def delete_pdf(self, r2_key: str) -> bool:
        """
        Delete PDF from R2 storage
        
        Args:
            r2_key: R2 storage key
            
        Returns:
            True if deleted successfully
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            logger.info(f"Deleting PDF from R2: {r2_key}")
            
            self.client.delete_object(
                Bucket=self._bucket_name,
                Key=r2_key
            )
            
            logger.info(f"PDF deleted successfully: {r2_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete PDF: {str(e)}")
            raise StorageError(
                message="Failed to delete PDF from storage",
                details={"r2_key": r2_key, "error": str(e)}
            )
    
    def file_exists(self, r2_key: str) -> bool:
        """
        Check if a file exists in R2 storage

        Args:
            r2_key: R2 storage key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self._bucket_name,
                Key=r2_key
            )
            return True
        except self.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {str(e)}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage

        Args:
            filename: Original filename string

        Returns:
            Sanitized filename safe for file systems
        """
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces and other whitespace with underscores
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Limit length to prevent overly long filenames
        sanitized = sanitized[:50] if len(sanitized) > 50 else sanitized
        # Ensure it's not empty
        return sanitized or "resume"

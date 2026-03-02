"""
Custom Exceptions
Application-specific exceptions for better error handling
"""

from typing import Optional, Any
from fastapi import HTTPException, status


class BaseAppException(Exception):
    """Base exception for all application errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(BaseAppException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundError(BaseAppException):
    """Resource not found errors"""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": str(resource_id)}
        )


class ValidationError(BaseAppException):
    """Validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ExternalServiceError(BaseAppException):
    """External service errors (AI, storage, etc.)"""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        details: Optional[dict] = None
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details or {"service": service_name}
        )


class AIServiceError(ExternalServiceError):
    """AI service specific errors"""
    
    def __init__(self, message: str = "AI service error", details: Optional[dict] = None):
        super().__init__(
            service_name="AI Service",
            message=message,
            details=details
        )


class StorageError(ExternalServiceError):
    """Storage service specific errors"""
    
    def __init__(self, message: str = "Storage service error", details: Optional[dict] = None):
        super().__init__(
            service_name="Storage Service",
            message=message,
            details=details
        )


class DatabaseError(BaseAppException):
    """Database related errors"""
    
    def __init__(self, message: str = "Database error", details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class PDFGenerationError(BaseAppException):
    """PDF generation errors"""
    
    def __init__(self, message: str = "PDF generation failed", details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ScrapingError(ExternalServiceError):
    """Web scraping errors"""
    
    def __init__(self, message: str = "Failed to scrape job description", details: Optional[dict] = None):
        super().__init__(
            service_name="Web Scraper",
            message=message,
            details=details
        )
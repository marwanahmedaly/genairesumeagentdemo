"""
Main Application
FastAPI application initialization and configuration
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .core.config import settings
from .core.logger import get_logger, setup_logging
from .api.routes import auth, resume, history, preferences
from .core.exceptions import BaseAppException

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Resume Optimizer AI Agent",
    description="AI-powered resume optimization and alignment service",
    version="2.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

logger.info(f"CORS configured for origins: {settings.cors_origins}")


# Register routers
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(history.router)
app.include_router(preferences.router)

logger.info("API routes registered")


# Exception handlers
@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Handle custom application exceptions
    
    Args:
        request: FastAPI request
        exc: BaseAppException instance
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            "error_type": exc.__class__.__name__,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI request validation errors
    
    Args:
        request: FastAPI request
        exc: RequestValidationError instance
        
    Returns:
        JSON response with validation errors
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error_type": "ValidationError",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_type": "InternalServerError",
            "details": {"error": str(exc)} if settings.is_development else None
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    
    Returns:
        Dictionary with API information
    """
    return {
        "name": "Resume Optimizer AI Agent",
        "version": "2.0.0",
        "environment": settings.environment,
        "docs": "/docs" if settings.is_development else None,
        "endpoints": {
            "POST /resume/full-alignment": "Complete resume alignment workflow",
            "GET /resume/generate-download-url": "Generate PDF download URL",
            "GET /history": "Get user's resume history",
            "DELETE /history/{record_id}": "Delete a resume record and PDF"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Dictionary with health status
    """
    return {
        "status": "healthy",
        "environment": settings.environment
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info("=" * 50)
    logger.info("Resume Optimizer AI Agent Starting...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"AI Model: {settings.ai_model}")
    logger.info(f"R2 Bucket: {settings.r2_bucket_name}")
    logger.info("=" * 50)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    logger.info("Resume Optimizer AI Agent Shutting down...")
    logger.info("=" * 50)


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
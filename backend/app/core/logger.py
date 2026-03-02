"""
Logging Configuration
Structured logging setup for the application
"""

import logging
import sys
from typing import Optional
from .config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        
    Returns:
        Configured logger instance
    """
    # Use settings or defaults
    level = log_level or settings.log_level
    
    # Define log format
    if log_format is None:
        if settings.is_development:
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
    
    # Get application logger
    logger = logging.getLogger("resume_agent")

    # Set log level for application logger
    logger.setLevel(level.upper())

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    # Remove any existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    # Create formatter
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
    
    # Log startup message
    logger.info(f"Logging initialized - Level: {level.upper()}, Environment: {settings.environment}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"resume_agent.{name}")


# Initialize logging on module import
_logger = setup_logging()
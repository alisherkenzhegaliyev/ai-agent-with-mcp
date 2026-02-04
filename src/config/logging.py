"""
Centralized logging configuration for the application.
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the entire application.
    
    Args:
        level: The logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: The name of the module (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

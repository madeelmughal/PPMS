"""
Logger configuration module
Sets up application-wide logging with file and console handlers.
"""

import logging
import os
from datetime import datetime
from src.config.firebase_config import AppConfig


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Set up logger with file and console handlers.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, AppConfig.LOG_LEVEL))

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    log_file = os.path.join(
        log_dir,
        f"ppms_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, AppConfig.LOG_LEVEL))
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, AppConfig.LOG_LEVEL))
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Create module-level logger
logger = setup_logger(__name__)

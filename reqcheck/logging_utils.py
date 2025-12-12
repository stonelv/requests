"""Logging utilities"""

import logging
import sys
from typing import Optional


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger("reqcheck")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name or "reqcheck")
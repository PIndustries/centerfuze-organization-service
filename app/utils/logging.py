"""
Logging utilities
"""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", service_name: Optional[str] = None) -> None:
    """Setup structured logging for the service"""
    
    # Map string level to logging level
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_mapping.get(level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set service name if provided
    if service_name:
        service_logger = logging.getLogger(service_name)
        service_logger.info(f"Logging initialized for {service_name}")
    
    # Reduce noise from third-party libraries
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("nats").setLevel(logging.INFO)
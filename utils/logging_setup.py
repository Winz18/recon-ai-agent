import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 3
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        log_level: Logging level (INFO, DEBUG...)
        log_file: Path to log file, None if only logging to console
        max_file_size: Maximum log file size
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger
    """
    # Create formatter with standard format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Set the log level (this will be overridden by the CLI utility but is 
    # needed for file logging)
    root_logger.setLevel(log_level)
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Check if a file handler already exists
        has_file_handler = False
        for handler in root_logger.handlers:
            if isinstance(handler, RotatingFileHandler) and handler.baseFilename == os.path.abspath(log_file):
                has_file_handler = True
                break
                
        # Create rotating file handler if needed
        if not has_file_handler:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
    
    # Note: We don't add a console handler here anymore
    # The CLI utility will handle console output
    
    # Set lower log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)
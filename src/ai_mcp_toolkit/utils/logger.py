"""Logging utilities for AI MCP Toolkit."""

import logging
import sys
from typing import Optional
from pathlib import Path
from rich.logging import RichHandler
import threading

_loggers = {}
_lock = threading.Lock()


def get_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Get or create a configured logger instance."""
    
    with _lock:
        if name in _loggers:
            return _loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create console handler with rich formatting
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=True,
        )
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        _loggers[name] = logger
        return logger


def configure_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure global logging settings."""
    # Remove default handlers
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    root_logger = get_logger("ai_mcp_toolkit", level, log_file)
    
    # Set up third-party library loggers
    logging.getLogger("ollama").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def set_log_level(level: str) -> None:
    """Set log level for all existing loggers."""
    log_level = getattr(logging, level.upper())
    
    with _lock:
        for logger in _loggers.values():
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)

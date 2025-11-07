"""Logging utilities for AI MCP Toolkit."""

import logging
import sys
import io
import time
from typing import Optional
from pathlib import Path
from rich.logging import RichHandler
import threading

_loggers = {}
_lock = threading.Lock()
_original_stderr = sys.stderr
_last_mongo_warning = 0


class MongoStderrFilter(io.TextIOBase):
    """Filter stderr to suppress verbose MongoDB background errors."""
    
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
        self.suppress_next_lines = 0
    
    def write(self, text: str) -> int:
        global _last_mongo_warning
        
        # Check if this is a MongoDB background task error
        if "MongoClient background task encountered an error" in text:
            self.suppress_next_lines = 100  # Suppress the next ~100 lines of traceback
            current_time = time.time()
            # Show friendly message only once per 30 seconds
            if current_time - _last_mongo_warning > 30:
                _last_mongo_warning = current_time
                self.original_stderr.write("\n⚠️  MongoDB connection interrupted (network/sleep). Will auto-reconnect.\n")
                self.original_stderr.flush()
            return len(text)
        
        # Suppress traceback lines if we're in suppression mode
        if self.suppress_next_lines > 0:
            self.suppress_next_lines -= 1
            # Only show the final pymongo.errors line
            if "pymongo.errors.AutoReconnect" in text:
                # Don't show it, we already showed friendly message
                self.suppress_next_lines = 0
            return len(text)
        
        # Pass through all other messages
        return self.original_stderr.write(text)
    
    def flush(self):
        return self.original_stderr.flush()
    
    def isatty(self):
        return self.original_stderr.isatty()


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


class MongoConnectionFilter(logging.Filter):
    """Filter to suppress verbose MongoDB connection errors and show friendly messages."""
    
    def __init__(self):
        super().__init__()
        self.last_warning_time = 0
        self.warning_interval = 30  # Show warning max once per 30 seconds
    
    def filter(self, record: logging.LogRecord) -> bool:
        import time
        
        # Suppress pymongo background task errors
        if "MongoClient background task" in str(record.msg):
            current_time = time.time()
            # Show a friendly warning only occasionally
            if current_time - self.last_warning_time > self.warning_interval:
                self.last_warning_time = current_time
                print("\n⚠️  MongoDB connection interrupted (computer may have been asleep). Connection will auto-reconnect.\n")
            return False  # Suppress the full traceback
        
        # Suppress socket.gaierror tracebacks
        if "socket.gaierror" in str(record.msg) or "nodename nor servname" in str(record.msg):
            return False
        
        # Suppress AutoReconnect tracebacks
        if "pymongo.errors.AutoReconnect" in str(record.msg):
            return False
        
        return True


def configure_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure global logging settings."""
    # Install stderr filter to catch MongoDB background errors (printed directly to stderr)
    if not isinstance(sys.stderr, MongoStderrFilter):
        sys.stderr = MongoStderrFilter(_original_stderr)
    
    # Remove default handlers
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    root_logger = get_logger("ai_mcp_toolkit", level, log_file)
    
    # Add MongoDB connection filter to root logger to catch background errors
    mongo_filter = MongoConnectionFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(mongo_filter)
    
    # Also add to pymongo logger specifically
    pymongo_logger = logging.getLogger("pymongo")
    pymongo_logger.addFilter(mongo_filter)
    pymongo_logger.setLevel(logging.WARNING)  # Reduce pymongo verbosity
    
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

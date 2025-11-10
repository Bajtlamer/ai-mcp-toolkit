"""Logging utilities for AI MCP Toolkit."""

import logging
import sys
import io
import time
from typing import Optional
from pathlib import Path
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler
import threading
import os

_loggers = {}
_lock = threading.Lock()
_original_stderr = sys.stderr
_last_mongo_warning = 0


class TeeStream(io.TextIOBase):
    """Stream that writes to both console and log file."""
    
    def __init__(self, console_stream, log_file_path: Optional[Path] = None):
        self.console_stream = console_stream
        self.log_file_path = log_file_path
        self.log_file = None
        
        if log_file_path:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            # Open in append mode with buffering
            self.log_file = open(log_file_path, 'a', encoding='utf-8', buffering=1)
    
    def write(self, text: str) -> int:
        # Write to console
        result = self.console_stream.write(text)
        
        # Also write to log file
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.write(text)
                self.log_file.flush()
            except Exception:
                pass  # Fail silently if log file write fails
        
        return result
    
    def flush(self):
        self.console_stream.flush()
        if self.log_file and not self.log_file.closed:
            self.log_file.flush()
    
    def close(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
    
    def isatty(self):
        return self.console_stream.isatty()


class MongoStderrFilter(io.TextIOBase):
    """Filter stderr to suppress verbose MongoDB background errors."""
    
    def __init__(self, original_stderr, log_to_file: bool = True):
        self.original_stderr = original_stderr
        self.buffer = []
        self.suppress_next_lines = 0
        self.log_to_file = log_to_file
    
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
    """Configure global logging settings with stdout/stderr capture to rotating log files."""
    
    # Set up log directory
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up stdout capture to file (keeps history)
    stdout_log = log_dir / "server_stdout.log"
    if not isinstance(sys.stdout, TeeStream):
        sys.stdout = TeeStream(sys.stdout, stdout_log)
    
    # Set up stderr with MongoDB filter AND file capture
    stderr_log = log_dir / "server_stderr.log"
    if not isinstance(sys.stderr, MongoStderrFilter):
        # First wrap with TeeStream for file logging
        tee_stderr = TeeStream(_original_stderr, stderr_log)
        # Then wrap with MongoDB filter
        sys.stderr = MongoStderrFilter(tee_stderr)
    
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


def rotate_logs(max_size_mb: int = 100, keep_backups: int = 5) -> None:
    """Rotate log files if they exceed max size.
    
    Args:
        max_size_mb: Maximum size in MB before rotation
        keep_backups: Number of backup files to keep
    """
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    if not log_dir.exists():
        return
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_size > max_size_bytes:
            # Rotate: .log -> .log.1, .log.1 -> .log.2, etc.
            for i in range(keep_backups - 1, 0, -1):
                old_backup = log_dir / f"{log_file.name}.{i}"
                new_backup = log_dir / f"{log_file.name}.{i + 1}"
                if old_backup.exists():
                    if new_backup.exists():
                        new_backup.unlink()
                    old_backup.rename(new_backup)
            
            # Move current log to .log.1
            backup = log_dir / f"{log_file.name}.1"
            if backup.exists():
                backup.unlink()
            log_file.rename(backup)
            
            # Create new empty log file
            log_file.touch()
            
            print(f"📝 Rotated log file: {log_file.name} (exceeded {max_size_mb}MB)")

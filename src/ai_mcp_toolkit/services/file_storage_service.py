"""Local file storage service for managing uploaded files."""

import os
import logging
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    Service for storing and retrieving uploaded files locally.
    
    Files are stored in the following structure:
    DATA_DIR/uploads/
        ├── {user_id}/
        │   ├── {year}/
        │   │   ├── {month}/
        │   │   │   ├── {uuid}.{ext}
        │   │   │   ├── {uuid}.{ext}
        
    This structure:
    - Isolates files by user
    - Organizes by upload date (year/month)
    - Uses UUID filenames to prevent conflicts
    - Preserves file extensions for MIME type detection
    """
    
    def __init__(self, base_storage_path: Optional[str] = None):
        """
        Initialize file storage service.
        
        Args:
            base_storage_path: Base directory for file storage
                              Default: ~/.ai-mcp-toolkit/uploads
        """
        if base_storage_path:
            self.base_path = Path(base_storage_path).expanduser()
        else:
            # Default to DATA_DIR/uploads
            data_dir = os.getenv("DATA_DIR", "~/.ai-mcp-toolkit")
            self.base_path = Path(data_dir).expanduser() / "uploads"
        
        # Ensure base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 FileStorageService initialized: {self.base_path}")
    
    def _get_user_path(self, user_id: str, year: Optional[int] = None, month: Optional[int] = None) -> Path:
        """
        Get storage path for a user, optionally with year/month subdirectories.
        
        Args:
            user_id: User ID
            year: Optional year (default: current year)
            month: Optional month (default: current month)
            
        Returns:
            Path object for the user's storage directory
        """
        if year is None or month is None:
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month
        
        user_path = self.base_path / user_id / str(year) / f"{month:02d}"
        user_path.mkdir(parents=True, exist_ok=True)
        
        return user_path
    
    def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str,
        file_id: Optional[str] = None
    ) -> dict:
        """
        Save a file to local storage.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename (used for extension extraction)
            user_id: User ID who owns the file
            file_id: Optional custom file ID (UUID will be generated if not provided)
            
        Returns:
            Dictionary with storage info:
            {
                'file_id': 'uuid-string',
                'file_path': '/full/path/to/file.ext',
                'relative_path': 'user_id/2025/01/uuid.ext',
                'size_bytes': 12345,
                'stored_at': '2025-01-03T12:00:00Z'
            }
        """
        try:
            # Generate file ID (UUID) if not provided
            if not file_id:
                file_id = str(uuid.uuid4())
            
            # Extract file extension from original filename
            file_ext = Path(filename).suffix or ''
            
            # Get user storage path (organized by year/month)
            user_path = self._get_user_path(user_id)
            
            # Create full filename: uuid.ext
            stored_filename = f"{file_id}{file_ext}"
            file_path = user_path / stored_filename
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Calculate relative path from base_path
            relative_path = file_path.relative_to(self.base_path)
            
            # Get file size
            size_bytes = len(file_bytes)
            
            logger.info(
                f"✅ Saved file: {filename} -> {stored_filename} "
                f"({size_bytes} bytes) for user {user_id}"
            )
            
            return {
                'file_id': file_id,
                'file_path': str(file_path),
                'relative_path': str(relative_path),
                'size_bytes': size_bytes,
                'stored_at': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving file {filename} for user {user_id}: {e}", exc_info=True)
            raise
    
    def get_file(self, file_id: str, user_id: str, year: Optional[int] = None, month: Optional[int] = None) -> Optional[bytes]:
        """
        Retrieve a file from local storage.
        
        Args:
            file_id: File UUID
            user_id: User ID who owns the file
            year: Optional year (will search if not provided)
            month: Optional month (will search if not provided)
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            # If year/month provided, look in that specific location
            if year and month:
                user_path = self._get_user_path(user_id, year, month)
                file_path = self._find_file_in_path(user_path, file_id)
                
                if file_path and file_path.exists():
                    with open(file_path, 'rb') as f:
                        return f.read()
            
            # Otherwise, search in user's directory tree
            user_base_path = self.base_path / user_id
            if not user_base_path.exists():
                logger.warning(f"User directory not found: {user_id}")
                return None
            
            # Search for file with matching file_id
            for file_path in user_base_path.rglob(f"{file_id}.*"):
                if file_path.is_file():
                    logger.info(f"📂 Found file: {file_path}")
                    with open(file_path, 'rb') as f:
                        return f.read()
            
            logger.warning(f"File not found: {file_id} for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error retrieving file {file_id} for user {user_id}: {e}", exc_info=True)
            return None
    
    def _find_file_in_path(self, directory: Path, file_id: str) -> Optional[Path]:
        """
        Find a file by ID in a directory (matches any extension).
        
        Args:
            directory: Directory to search
            file_id: File UUID to find
            
        Returns:
            Path to file if found, None otherwise
        """
        if not directory.exists():
            return None
        
        for file_path in directory.glob(f"{file_id}.*"):
            if file_path.is_file():
                return file_path
        
        return None
    
    def delete_file(self, file_id: str, user_id: str) -> bool:
        """
        Delete a file from local storage.
        
        Args:
            file_id: File UUID
            user_id: User ID who owns the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Search for file in user's directory
            user_base_path = self.base_path / user_id
            if not user_base_path.exists():
                logger.warning(f"User directory not found: {user_id}")
                return False
            
            # Find and delete file
            for file_path in user_base_path.rglob(f"{file_id}.*"):
                if file_path.is_file():
                    file_path.unlink()
                    logger.info(f"🗑️ Deleted file: {file_path}")
                    return True
            
            logger.warning(f"File not found for deletion: {file_id} for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting file {file_id} for user {user_id}: {e}", exc_info=True)
            return False
    
    def file_exists(self, file_id: str, user_id: str) -> bool:
        """
        Check if a file exists in local storage.
        
        Args:
            file_id: File UUID
            user_id: User ID who owns the file
            
        Returns:
            True if file exists, False otherwise
        """
        user_base_path = self.base_path / user_id
        if not user_base_path.exists():
            return False
        
        for file_path in user_base_path.rglob(f"{file_id}.*"):
            if file_path.is_file():
                return True
        
        return False
    
    def get_file_path(self, file_id: str, user_id: str) -> Optional[str]:
        """
        Get the full file path for a stored file.
        
        Args:
            file_id: File UUID
            user_id: User ID who owns the file
            
        Returns:
            Full file path as string, or None if not found
        """
        user_base_path = self.base_path / user_id
        if not user_base_path.exists():
            return None
        
        for file_path in user_base_path.rglob(f"{file_id}.*"):
            if file_path.is_file():
                return str(file_path)
        
        return None
    
    def get_storage_stats(self, user_id: Optional[str] = None) -> dict:
        """
        Get storage statistics.
        
        Args:
            user_id: Optional user ID to get stats for (if None, returns total stats)
            
        Returns:
            Dictionary with storage stats:
            {
                'total_files': 123,
                'total_size_bytes': 1234567,
                'total_size_mb': 1.18
            }
        """
        try:
            if user_id:
                base_path = self.base_path / user_id
            else:
                base_path = self.base_path
            
            if not base_path.exists():
                return {
                    'total_files': 0,
                    'total_size_bytes': 0,
                    'total_size_mb': 0.0
                }
            
            total_files = 0
            total_size = 0
            
            for file_path in base_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting storage stats: {e}", exc_info=True)
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0.0
            }


# Global instance
_file_storage_service = None


def get_file_storage_service(base_path: Optional[str] = None) -> FileStorageService:
    """
    Get or create the global FileStorageService instance.
    
    Args:
        base_path: Optional base storage path (only used on first call)
        
    Returns:
        FileStorageService instance
    """
    global _file_storage_service
    
    if _file_storage_service is None:
        _file_storage_service = FileStorageService(base_path)
    
    return _file_storage_service

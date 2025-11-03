"""File storage service for managing uploaded files."""

import logging
import os
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..utils.config import Config

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for storing and retrieving uploaded files."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize file storage service."""
        self.config = config or Config()
        self.storage_dir = self.config.data_dir / "uploads"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileStorageService initialized with storage_dir: {self.storage_dir}")
    
    def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str,
        resource_id: str
    ) -> str:
        """
        Save a file to disk.
        
        Args:
            file_bytes: File content
            filename: Original filename
            user_id: User ID
            resource_id: Resource ID for organization
            
        Returns:
            Relative file path where file was saved
        """
        try:
            # Create directory structure: uploads/{user_id}/{year}/{month}/
            now = datetime.utcnow()
            user_dir = self.storage_dir / user_id / str(now.year) / f"{now.month:02d}"
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean filename
            clean_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
            
            # Create full path: {resource_id}_{filename}
            file_path = user_dir / f"{resource_id}_{clean_filename}"
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Return relative path from storage_dir
            relative_path = str(file_path.relative_to(self.storage_dir))
            
            logger.info(f"Saved file: {relative_path} ({len(file_bytes)} bytes)")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}", exc_info=True)
            raise
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve a file from storage.
        
        Args:
            file_path: Relative file path
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            full_path = self.storage_dir / file_path
            
            if not full_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Retrieved file: {file_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving file {file_path}: {e}", exc_info=True)
            return None
    
    def get_file_base64(self, file_path: str) -> Optional[str]:
        """
        Retrieve a file and encode as base64.
        
        Args:
            file_path: Relative file path
            
        Returns:
            Base64 encoded file content, or None if not found
        """
        content = self.get_file(file_path)
        if content:
            return base64.b64encode(content).decode('utf-8')
        return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Relative file path
            
        Returns:
            True if deleted, False if not found
        """
        try:
            full_path = self.storage_dir / file_path
            
            if not full_path.exists():
                logger.warning(f"File not found for deletion: {file_path}")
                return False
            
            full_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}", exc_info=True)
            return False


# Singleton instance
_file_storage_service = None


def get_file_storage_service(config: Optional[Config] = None) -> FileStorageService:
    """Get or create the singleton FileStorageService instance."""
    global _file_storage_service
    if _file_storage_service is None:
        _file_storage_service = FileStorageService(config)
    return _file_storage_service

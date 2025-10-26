"""Audit logging utilities for tracking user operations."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.documents import AuditLog, User

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger for tracking user operations."""
    
    @staticmethod
    async def log(
        user: User,
        action: str,
        method: str,
        endpoint: str,
        status_code: int,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log a user operation to the audit log.
        
        Args:
            user: User performing the action
            action: Action identifier (e.g., "resource.create", "auth.login")
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            resource_type: Optional resource type
            resource_id: Optional resource ID
            ip_address: Client IP address
            user_agent: Client user agent
            request_data: Sanitized request data
            response_data: Sanitized response data
            error_message: Error message if any
            duration_ms: Request duration in milliseconds
        """
        try:
            # Sanitize sensitive data
            sanitized_request = AuditLogger._sanitize_data(request_data)
            sanitized_response = AuditLogger._sanitize_data(response_data)
            
            audit_log = AuditLog(
                user_id=str(user.id),
                username=user.username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=sanitized_request,
                response_data=sanitized_response,
                error_message=error_message,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
            await audit_log.save()
            
        except Exception as e:
            logger.error(f"Error logging audit entry: {e}", exc_info=True)
    
    @staticmethod
    def _sanitize_data(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitize data by removing sensitive fields.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if not data:
            return None
        
        # Fields to remove from logs
        sensitive_fields = {
            'password',
            'password_hash',
            'token',
            'secret',
            'api_key',
            'access_token',
            'refresh_token'
        }
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = AuditLogger._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    async def get_user_logs(
        user_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of logs to return
            skip: Number of logs to skip
            
        Returns:
            List of audit logs
        """
        try:
            logs = await AuditLog.find(
                AuditLog.user_id == user_id
            ).sort(-AuditLog.timestamp).skip(skip).limit(limit).to_list()
            
            return logs
            
        except Exception as e:
            logger.error(f"Error fetching user logs: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_all_logs(
        limit: int = 100,
        skip: int = 0,
        action: Optional[str] = None
    ) -> list[AuditLog]:
        """
        Get all audit logs (admin only).
        
        Args:
            limit: Maximum number of logs to return
            skip: Number of logs to skip
            action: Optional action filter
            
        Returns:
            List of audit logs
        """
        try:
            query = {}
            if action:
                query["action"] = action
            
            logs = await AuditLog.find(query).sort(
                -AuditLog.timestamp
            ).skip(skip).limit(limit).to_list()
            
            return logs
            
        except Exception as e:
            logger.error(f"Error fetching all logs: {e}", exc_info=True)
            return []

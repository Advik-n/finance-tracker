"""
Audit Logger Middleware

Logs all API requests for security and debugging purposes.
"""

import logging
import time
import uuid
from typing import Callable, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


class AuditEventType(str, Enum):
    """Types of audit events."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    AUTH = "auth"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditContext:
    """Context for audit events."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    request_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[AuditContext] = None
    details: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Audit logger for recording security and access events."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        log_data = {
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "message": event.message,
            "request_id": event.request_id,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details,
        }
        if event.context:
            log_data["context"] = {
                "user_id": event.context.user_id,
                "session_id": event.context.session_id,
                "ip_address": event.context.ip_address,
            }
        self.logger.info(str(log_data))
    
    def log_request(self, request_id: str, method: str, path: str, 
                    ip_address: str, user_id: Optional[str] = None) -> None:
        """Log an API request."""
        event = AuditEvent(
            event_type=AuditEventType.REQUEST,
            severity=AuditSeverity.LOW,
            message=f"API Request: {method} {path}",
            request_id=request_id,
            context=AuditContext(user_id=user_id, ip_address=ip_address),
            details={"method": method, "path": path}
        )
        self.log_event(event)
    
    def log_auth_event(self, request_id: str, action: str, 
                       success: bool, user_id: Optional[str] = None,
                       ip_address: Optional[str] = None) -> None:
        """Log an authentication event."""
        severity = AuditSeverity.MEDIUM if success else AuditSeverity.HIGH
        event = AuditEvent(
            event_type=AuditEventType.AUTH,
            severity=severity,
            message=f"Auth {action}: {'success' if success else 'failed'}",
            request_id=request_id,
            context=AuditContext(user_id=user_id, ip_address=ip_address),
            details={"action": action, "success": success}
        )
        self.log_event(event)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all API requests.
    
    Records request details, response status, and timing
    for security auditing and debugging.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Log request and response details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Record start time
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Get request details
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        audit_logger.info(
            f"REQUEST | {request_id} | {client_ip} | {method} {path}"
            f"{('?' + query) if query else ''}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log response
            audit_logger.info(
                f"RESPONSE | {request_id} | {response.status_code} | "
                f"{duration_ms}ms | {method} {path}"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log error
            audit_logger.error(
                f"ERROR | {request_id} | {type(e).__name__} | "
                f"{duration_ms}ms | {method} {path} | {str(e)}"
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

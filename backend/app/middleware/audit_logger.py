"""
Audit Logger Middleware

Logs all API requests for security and debugging purposes.
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


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

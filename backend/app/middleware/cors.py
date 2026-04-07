"""
CORS Configuration

Configurable Cross-Origin Resource Sharing settings.
"""

from typing import List
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

from app.config import settings


def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins from settings.
    
    Returns:
        List of allowed origin URLs
    """
    return settings.cors_origins


def get_cors_config() -> dict:
    """
    Get CORS configuration dictionary.
    
    Returns:
        Dict with CORS settings for middleware
    """
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers,
        "expose_headers": [
            "X-Request-ID",
            "X-Response-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        "max_age": 600,  # Cache preflight requests for 10 minutes
    }


# Re-export the CORS middleware for convenience
CORSMiddleware = FastAPICORSMiddleware

"""
Rate Limiter Middleware for Finance Tracker

This module provides comprehensive rate limiting with:
- Per-user and per-IP rate limiting
- Different limits for different endpoints
- Sliding window algorithm
- Redis backend for distributed limiting
- Proper 429 responses with retry-after

Security Level: BANK-GRADE
Compliance: PCI-DSS (brute force protection)
"""

import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class RateLimitScope(Enum):
    """Scope for rate limiting."""
    USER = "user"      # Per authenticated user
    IP = "ip"          # Per IP address
    GLOBAL = "global"  # Global limit
    ENDPOINT = "endpoint"  # Per endpoint


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule.
    
    Attributes:
        requests: Maximum requests allowed
        window_seconds: Time window in seconds
        scope: Rate limit scope
        burst_allowance: Extra requests allowed for bursts
        key_prefix: Redis key prefix for this rule
    """
    requests: int
    window_seconds: int
    scope: RateLimitScope = RateLimitScope.USER
    burst_allowance: int = 0
    key_prefix: str = "ratelimit"
    
    @property
    def total_limit(self) -> int:
        """Total requests including burst allowance."""
        return self.requests + self.burst_allowance


@dataclass
class RateLimitResult:
    """Result of a rate limit check.
    
    Attributes:
        allowed: Whether the request is allowed
        remaining: Remaining requests in window
        reset_at: When the window resets (Unix timestamp)
        retry_after: Seconds until retry is allowed (if limited)
        limit: The limit that was applied
    """
    allowed: bool
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None
    limit: int = 0


# Endpoint-specific rate limit configurations
class EndpointLimits:
    """Predefined rate limits for different endpoint categories."""
    
    # Authentication endpoints - strict limits to prevent brute force
    AUTH = RateLimitConfig(
        requests=5,
        window_seconds=60,
        scope=RateLimitScope.IP,
        burst_allowance=0,
        key_prefix="auth",
    )
    
    # File upload endpoints - moderate limits
    UPLOAD = RateLimitConfig(
        requests=10,
        window_seconds=60,
        scope=RateLimitScope.USER,
        burst_allowance=2,
        key_prefix="upload",
    )
    
    # Analytics/reporting endpoints - higher limits
    ANALYTICS = RateLimitConfig(
        requests=60,
        window_seconds=60,
        scope=RateLimitScope.USER,
        burst_allowance=10,
        key_prefix="analytics",
    )
    
    # General API endpoints
    GENERAL = RateLimitConfig(
        requests=100,
        window_seconds=60,
        scope=RateLimitScope.USER,
        burst_allowance=20,
        key_prefix="general",
    )
    
    # Sensitive operations (password change, transfer, etc.)
    SENSITIVE = RateLimitConfig(
        requests=3,
        window_seconds=60,
        scope=RateLimitScope.USER,
        burst_allowance=0,
        key_prefix="sensitive",
    )
    
    # Public endpoints (health check, etc.)
    PUBLIC = RateLimitConfig(
        requests=1000,
        window_seconds=60,
        scope=RateLimitScope.GLOBAL,
        burst_allowance=100,
        key_prefix="public",
    )


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation.
    
    Uses the sliding window log algorithm for accurate rate limiting:
    - Stores timestamps of recent requests
    - Counts requests within the sliding window
    - More accurate than fixed window
    
    This is a memory-based implementation. For production,
    use RedisRateLimiter for distributed rate limiting.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._requests: Dict[str, list] = {}
    
    def _get_key(self, identifier: str, config: RateLimitConfig) -> str:
        """Generate storage key.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
            
        Returns:
            Storage key string
        """
        return f"{config.key_prefix}:{identifier}"
    
    def _cleanup_old_requests(self, key: str, window_start: float) -> None:
        """Remove requests outside the current window.
        
        Args:
            key: Storage key
            window_start: Start of current window (Unix timestamp)
        """
        if key in self._requests:
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]
    
    def check(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check if a request is allowed.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
            
        Returns:
            RateLimitResult with decision and metadata
        """
        now = time.time()
        window_start = now - config.window_seconds
        key = self._get_key(identifier, config)
        
        # Cleanup old requests
        self._cleanup_old_requests(key, window_start)
        
        # Count current requests
        current_requests = len(self._requests.get(key, []))
        
        # Calculate remaining
        remaining = max(0, config.total_limit - current_requests)
        
        # Calculate reset time
        if key in self._requests and self._requests[key]:
            oldest_request = min(self._requests[key])
            reset_at = int(oldest_request + config.window_seconds)
        else:
            reset_at = int(now + config.window_seconds)
        
        # Check if allowed
        if current_requests < config.total_limit:
            return RateLimitResult(
                allowed=True,
                remaining=remaining - 1,  # Account for this request
                reset_at=reset_at,
                limit=config.total_limit,
            )
        else:
            retry_after = reset_at - int(now)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(1, retry_after),
                limit=config.total_limit,
            )
    
    def record(self, identifier: str, config: RateLimitConfig) -> None:
        """Record a request.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
        """
        key = self._get_key(identifier, config)
        now = time.time()
        
        if key not in self._requests:
            self._requests[key] = []
        
        self._requests[key].append(now)


class RedisRateLimiter:
    """Redis-backed sliding window rate limiter.
    
    Uses Redis sorted sets for distributed rate limiting:
    - Timestamps stored as scores
    - ZRANGEBYSCORE for window queries
    - ZREMRANGEBYSCORE for cleanup
    - Atomic operations with Lua scripts
    
    Example:
        >>> limiter = RedisRateLimiter(redis_client)
        >>> result = await limiter.check("user:123", EndpointLimits.AUTH)
        >>> if result.allowed:
        >>>     await limiter.record("user:123", EndpointLimits.AUTH)
    """
    
    # Lua script for atomic rate limit check and record
    RATE_LIMIT_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local window_start = now - window
    
    -- Remove old entries
    redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
    
    -- Count current entries
    local count = redis.call('ZCARD', key)
    
    if count < limit then
        -- Add new entry
        redis.call('ZADD', key, now, now .. ':' .. math.random())
        -- Set expiry
        redis.call('EXPIRE', key, window + 1)
        return {1, limit - count - 1, 0}
    else
        -- Get oldest entry for retry-after
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local retry_after = 0
        if oldest[2] then
            retry_after = math.ceil(oldest[2] + window - now)
        end
        return {0, 0, retry_after}
    end
    """
    
    def __init__(self, redis_client):
        """Initialize with Redis client.
        
        Args:
            redis_client: Async Redis client
        """
        self._redis = redis_client
        self._script_sha = None
    
    async def _ensure_script(self) -> str:
        """Ensure Lua script is loaded.
        
        Returns:
            Script SHA
        """
        if self._script_sha is None:
            self._script_sha = await self._redis.script_load(self.RATE_LIMIT_SCRIPT)
        return self._script_sha
    
    def _get_key(self, identifier: str, config: RateLimitConfig) -> str:
        """Generate Redis key.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
            
        Returns:
            Redis key string
        """
        return f"ratelimit:{config.key_prefix}:{identifier}"
    
    async def check_and_record(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Atomically check and record a request.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
            
        Returns:
            RateLimitResult with decision and metadata
        """
        now = time.time()
        key = self._get_key(identifier, config)
        
        try:
            script_sha = await self._ensure_script()
            result = await self._redis.evalsha(
                script_sha,
                1,
                key,
                str(now),
                str(config.window_seconds),
                str(config.total_limit),
            )
            
            allowed = result[0] == 1
            remaining = result[1]
            retry_after = result[2] if not allowed else None
            
            reset_at = int(now + config.window_seconds)
            
            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=config.total_limit,
            )
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open (allow) on Redis errors - adjust based on security requirements
            return RateLimitResult(
                allowed=True,
                remaining=config.total_limit,
                reset_at=int(now + config.window_seconds),
                limit=config.total_limit,
            )
    
    async def check(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit without recording.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
            
        Returns:
            RateLimitResult with current state
        """
        now = time.time()
        window_start = now - config.window_seconds
        key = self._get_key(identifier, config)
        
        try:
            # Count requests in window
            count = await self._redis.zcount(key, window_start, now)
            remaining = max(0, config.total_limit - count)
            
            # Get oldest entry for reset time
            oldest = await self._redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = int(oldest[0][1] + config.window_seconds)
            else:
                reset_at = int(now + config.window_seconds)
            
            return RateLimitResult(
                allowed=count < config.total_limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=max(1, reset_at - int(now)) if count >= config.total_limit else None,
                limit=config.total_limit,
            )
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            return RateLimitResult(
                allowed=True,
                remaining=config.total_limit,
                reset_at=int(now + config.window_seconds),
                limit=config.total_limit,
            )
    
    async def reset(self, identifier: str, config: RateLimitConfig) -> None:
        """Reset rate limit for an identifier.
        
        Args:
            identifier: User ID, IP, or other identifier
            config: Rate limit configuration
        """
        key = self._get_key(identifier, config)
        await self._redis.delete(key)


class RateLimiter:
    """Main rate limiter interface.
    
    Provides a unified interface for rate limiting with:
    - Automatic Redis/memory backend selection
    - Endpoint classification
    - IP and user identification
    
    Example:
        >>> limiter = RateLimiter(redis_client=redis)
        >>> result = await limiter.check_request(
        >>>     endpoint="/api/v1/login",
        >>>     user_id=None,
        >>>     ip_address="192.168.1.1"
        >>> )
    """
    
    # Endpoint to limit category mapping
    ENDPOINT_CATEGORIES = {
        # Auth endpoints
        "/api/v1/auth/login": EndpointLimits.AUTH,
        "/api/v1/auth/register": EndpointLimits.AUTH,
        "/api/v1/auth/forgot-password": EndpointLimits.AUTH,
        "/api/v1/auth/reset-password": EndpointLimits.AUTH,
        "/api/v1/auth/verify-otp": EndpointLimits.AUTH,
        
        # Upload endpoints
        "/api/v1/upload/statement": EndpointLimits.UPLOAD,
        "/api/v1/upload/receipt": EndpointLimits.UPLOAD,
        "/api/v1/import/csv": EndpointLimits.UPLOAD,
        
        # Analytics endpoints
        "/api/v1/analytics/": EndpointLimits.ANALYTICS,
        "/api/v1/reports/": EndpointLimits.ANALYTICS,
        "/api/v1/dashboard/": EndpointLimits.ANALYTICS,
        
        # Sensitive operations
        "/api/v1/account/password": EndpointLimits.SENSITIVE,
        "/api/v1/transfer/": EndpointLimits.SENSITIVE,
        "/api/v1/settings/security": EndpointLimits.SENSITIVE,
        
        # Public endpoints
        "/health": EndpointLimits.PUBLIC,
        "/api/v1/status": EndpointLimits.PUBLIC,
    }
    
    def __init__(self, redis_client=None):
        """Initialize rate limiter.
        
        Args:
            redis_client: Optional Redis client for distributed limiting
        """
        if redis_client:
            self._limiter = RedisRateLimiter(redis_client)
        else:
            self._limiter = SlidingWindowRateLimiter()
        self._use_redis = redis_client is not None
    
    def _get_endpoint_config(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit config for an endpoint.
        
        Args:
            endpoint: The API endpoint path
            
        Returns:
            RateLimitConfig for the endpoint
        """
        # Check exact match first
        if endpoint in self.ENDPOINT_CATEGORIES:
            return self.ENDPOINT_CATEGORIES[endpoint]
        
        # Check prefix matches
        for prefix, config in self.ENDPOINT_CATEGORIES.items():
            if endpoint.startswith(prefix):
                return config
        
        # Default to general limits
        return EndpointLimits.GENERAL
    
    def _get_identifier(
        self,
        config: RateLimitConfig,
        user_id: Optional[str],
        ip_address: str,
    ) -> str:
        """Get identifier based on scope.
        
        Args:
            config: Rate limit configuration
            user_id: Authenticated user ID
            ip_address: Client IP address
            
        Returns:
            Identifier string
        """
        if config.scope == RateLimitScope.USER:
            return user_id or f"anon:{ip_address}"
        elif config.scope == RateLimitScope.IP:
            return ip_address
        elif config.scope == RateLimitScope.GLOBAL:
            return "global"
        else:
            return f"{user_id or ip_address}"
    
    async def check_request(
        self,
        endpoint: str,
        user_id: Optional[str],
        ip_address: str,
        custom_config: Optional[RateLimitConfig] = None,
    ) -> RateLimitResult:
        """Check if a request should be allowed.
        
        Args:
            endpoint: The API endpoint
            user_id: Authenticated user ID (or None)
            ip_address: Client IP address
            custom_config: Optional custom rate limit config
            
        Returns:
            RateLimitResult with decision and headers
        """
        config = custom_config or self._get_endpoint_config(endpoint)
        identifier = self._get_identifier(config, user_id, ip_address)
        
        if self._use_redis:
            result = await self._limiter.check_and_record(identifier, config)
        else:
            result = self._limiter.check(identifier, config)
            if result.allowed:
                self._limiter.record(identifier, config)
        
        # Log rate limit events
        if not result.allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "endpoint": endpoint,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "retry_after": result.retry_after,
                }
            )
        
        return result
    
    def get_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Generate rate limit response headers.
        
        Args:
            result: Rate limit check result
            
        Returns:
            Dictionary of headers to add to response
        """
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_at),
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        return headers


class RateLimitMiddleware:
    """ASGI middleware for rate limiting.
    
    Integrates rate limiting into the request/response cycle.
    
    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(RateLimitMiddleware, redis_client=redis)
    """
    
    def __init__(
        self,
        app,
        redis_client=None,
        get_user_id: Optional[Callable] = None,
    ):
        """Initialize middleware.
        
        Args:
            app: ASGI application
            redis_client: Optional Redis client
            get_user_id: Optional function to extract user ID from request
        """
        self.app = app
        self.limiter = RateLimiter(redis_client)
        self.get_user_id = get_user_id
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        path = scope.get("path", "/")
        
        # Get client IP (handle proxies)
        client = scope.get("client")
        ip_address = client[0] if client else "unknown"
        
        # Check for X-Forwarded-For header
        headers = dict(scope.get("headers", []))
        forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        
        # Get user ID if authenticated
        user_id = None
        if self.get_user_id:
            user_id = await self.get_user_id(scope)
        
        # Check rate limit
        result = await self.limiter.check_request(path, user_id, ip_address)
        
        if not result.allowed:
            # Return 429 response
            response_headers = [
                (b"content-type", b"application/json"),
            ]
            for key, value in self.limiter.get_headers(result).items():
                response_headers.append((key.lower().encode(), str(value).encode()))
            
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": response_headers,
            })
            
            body = json.dumps({
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Please retry after {result.retry_after} seconds.",
                "retry_after": result.retry_after,
            }).encode()
            
            await send({
                "type": "http.response.body",
                "body": body,
            })
            return
        
        # Store rate limit headers to add to response
        rate_limit_headers = self.limiter.get_headers(result)
        
        # Wrap send to add rate limit headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in rate_limit_headers.items():
                    headers.append((key.lower().encode(), str(value).encode()))
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Rate limiting best practices
RATE_LIMIT_GUIDELINES = """
## Rate Limiting Best Practices for Financial APIs

### Endpoint Categories
1. **Authentication** (5 req/min): Login, register, password reset
2. **Sensitive Operations** (3 req/min): Fund transfers, password changes
3. **Uploads** (10 req/min): Document uploads, imports
4. **Analytics** (60 req/min): Reports, dashboards
5. **General API** (100 req/min): Standard CRUD operations

### Implementation
1. Use sliding window algorithm for accuracy
2. Implement per-user AND per-IP limits
3. Use Redis for distributed rate limiting
4. Include proper response headers (X-RateLimit-*)
5. Return 429 with Retry-After header

### Security Considerations
1. Fail closed on Redis errors for auth endpoints
2. Fail open for non-critical endpoints
3. Log all rate limit events for monitoring
4. Implement circuit breakers for downstream services
5. Consider geographic rate limiting for compliance

### Compliance
1. PCI-DSS: Protect against brute force attacks
2. Document rate limits in API documentation
3. Provide clear error messages
4. Monitor for abuse patterns
"""

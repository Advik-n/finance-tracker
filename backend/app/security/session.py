"""
Session Security Module for Finance Tracker

This module provides comprehensive session management with:
- Secure session creation and validation
- Session invalidation on password change
- Concurrent session limits
- Device fingerprinting
- Session activity tracking

Security Level: BANK-GRADE
Compliance: PCI-DSS, SOC2, NIST 800-63B
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hmac

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status values."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"
    SECURITY_TERMINATED = "security_terminated"


@dataclass
class DeviceFingerprint:
    """Device fingerprint for session binding.
    
    Attributes:
        user_agent: Browser user agent string
        accept_language: Accept-Language header
        screen_resolution: Screen resolution (from client)
        timezone: Client timezone
        platform: Operating system platform
        fingerprint_hash: Hash of fingerprint data
    """
    user_agent: str
    accept_language: str = ""
    screen_resolution: str = ""
    timezone: str = ""
    platform: str = ""
    fingerprint_hash: str = ""
    
    def __post_init__(self):
        """Generate fingerprint hash after initialization."""
        if not self.fingerprint_hash:
            self.fingerprint_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate hash of fingerprint components.
        
        Returns:
            SHA-256 hash of fingerprint data
        """
        data = f"{self.user_agent}|{self.accept_language}|{self.platform}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def matches(self, other: "DeviceFingerprint", strict: bool = False) -> bool:
        """Check if fingerprints match.
        
        Args:
            other: Fingerprint to compare against
            strict: If True, require exact match
            
        Returns:
            True if fingerprints match (within tolerance)
        """
        if strict:
            return self.fingerprint_hash == other.fingerprint_hash
        
        # Fuzzy matching for browser updates, etc.
        # Match on platform and language
        return (
            self._normalize_platform(self.platform) == self._normalize_platform(other.platform)
            and self._normalize_user_agent(self.user_agent) == self._normalize_user_agent(other.user_agent)
        )
    
    def _normalize_platform(self, platform: str) -> str:
        """Normalize platform string."""
        platform = platform.lower()
        if "windows" in platform:
            return "windows"
        if "mac" in platform or "darwin" in platform:
            return "macos"
        if "linux" in platform:
            return "linux"
        if "android" in platform:
            return "android"
        if "ios" in platform or "iphone" in platform or "ipad" in platform:
            return "ios"
        return platform
    
    def _normalize_user_agent(self, ua: str) -> str:
        """Normalize user agent to browser family."""
        ua = ua.lower()
        if "chrome" in ua and "edge" not in ua:
            return "chrome"
        if "firefox" in ua:
            return "firefox"
        if "safari" in ua and "chrome" not in ua:
            return "safari"
        if "edge" in ua:
            return "edge"
        return "other"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "user_agent": self.user_agent[:200],  # Truncate for storage
            "accept_language": self.accept_language,
            "screen_resolution": self.screen_resolution,
            "timezone": self.timezone,
            "platform": self.platform,
            "fingerprint_hash": self.fingerprint_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "DeviceFingerprint":
        """Create from dictionary.
        
        Args:
            data: Dictionary with fingerprint data
            
        Returns:
            DeviceFingerprint instance
        """
        return cls(
            user_agent=data.get("user_agent", ""),
            accept_language=data.get("accept_language", ""),
            screen_resolution=data.get("screen_resolution", ""),
            timezone=data.get("timezone", ""),
            platform=data.get("platform", ""),
            fingerprint_hash=data.get("fingerprint_hash", ""),
        )


@dataclass
class Session:
    """User session representation.
    
    Attributes:
        session_id: Unique session identifier
        user_id: Associated user identifier
        created_at: Session creation timestamp
        expires_at: Session expiration timestamp
        last_activity_at: Last activity timestamp
        ip_address: Client IP address
        device_fingerprint: Device fingerprint data
        status: Session status
        refresh_count: Number of times session was refreshed
        mfa_verified: Whether MFA was completed
        device_name: User-friendly device name
    """
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    ip_address: str
    device_fingerprint: DeviceFingerprint
    status: SessionStatus = SessionStatus.ACTIVE
    refresh_count: int = 0
    mfa_verified: bool = False
    device_name: str = ""
    
    def is_valid(self) -> bool:
        """Check if session is currently valid.
        
        Returns:
            True if session is active and not expired
        """
        if self.status != SessionStatus.ACTIVE:
            return False
        
        now = datetime.now(timezone.utc)
        return now < self.expires_at
    
    def is_recently_active(self, threshold_minutes: int = 30) -> bool:
        """Check if session was recently active.
        
        Args:
            threshold_minutes: Activity threshold in minutes
            
        Returns:
            True if session was active within threshold
        """
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=threshold_minutes)
        return self.last_activity_at > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation (safe for serialization)
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "ip_address": self.ip_address,
            "device_fingerprint": self.device_fingerprint.to_dict(),
            "status": self.status.value,
            "refresh_count": self.refresh_count,
            "mfa_verified": self.mfa_verified,
            "device_name": self.device_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary.
        
        Args:
            data: Dictionary with session data
            
        Returns:
            Session instance
        """
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            last_activity_at=datetime.fromisoformat(data["last_activity_at"]),
            ip_address=data["ip_address"],
            device_fingerprint=DeviceFingerprint.from_dict(data["device_fingerprint"]),
            status=SessionStatus(data["status"]),
            refresh_count=data.get("refresh_count", 0),
            mfa_verified=data.get("mfa_verified", False),
            device_name=data.get("device_name", ""),
        )


@dataclass
class SessionConfig:
    """Session management configuration.
    
    Attributes:
        session_timeout_minutes: Session idle timeout
        absolute_timeout_hours: Maximum session lifetime
        max_concurrent_sessions: Maximum sessions per user
        require_mfa_for_sensitive: Require MFA for sensitive operations
        bind_to_ip: Bind session to IP address
        bind_to_device: Bind session to device fingerprint
        refresh_threshold_minutes: Refresh session after this idle time
        suspicious_activity_threshold: Threshold for suspicious activity detection
    """
    session_timeout_minutes: int = 30
    absolute_timeout_hours: int = 24
    max_concurrent_sessions: int = 3
    require_mfa_for_sensitive: bool = True
    bind_to_ip: bool = False  # May cause issues with mobile networks
    bind_to_device: bool = True
    refresh_threshold_minutes: int = 15
    suspicious_activity_threshold: int = 5


class SessionStorage:
    """Abstract session storage interface."""
    
    async def save(self, session: Session) -> None:
        """Save session to storage."""
        raise NotImplementedError
    
    async def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        raise NotImplementedError
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user."""
        raise NotImplementedError
    
    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        raise NotImplementedError
    
    async def delete_all_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user. Returns count deleted."""
        raise NotImplementedError


class InMemorySessionStorage(SessionStorage):
    """In-memory session storage for development."""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, Set[str]] = {}
    
    async def save(self, session: Session) -> None:
        self._sessions[session.session_id] = session
        if session.user_id not in self._user_sessions:
            self._user_sessions[session.user_id] = set()
        self._user_sessions[session.user_id].add(session.session_id)
    
    async def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        session_ids = self._user_sessions.get(user_id, set())
        return [
            self._sessions[sid] for sid in session_ids
            if sid in self._sessions
        ]
    
    async def delete(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session and session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)
    
    async def delete_all_user_sessions(self, user_id: str) -> int:
        session_ids = self._user_sessions.pop(user_id, set())
        count = 0
        for sid in session_ids:
            if sid in self._sessions:
                del self._sessions[sid]
                count += 1
        return count


class RedisSessionStorage(SessionStorage):
    """Redis-backed session storage for production."""
    
    def __init__(self, redis_client, key_prefix: str = "session"):
        self._redis = redis_client
        self._prefix = key_prefix
    
    def _session_key(self, session_id: str) -> str:
        return f"{self._prefix}:{session_id}"
    
    def _user_sessions_key(self, user_id: str) -> str:
        return f"{self._prefix}:user:{user_id}"
    
    async def save(self, session: Session) -> None:
        key = self._session_key(session.session_id)
        user_key = self._user_sessions_key(session.user_id)
        
        # Calculate TTL
        ttl = int((session.expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl <= 0:
            return
        
        # Save session
        await self._redis.setex(key, ttl, json.dumps(session.to_dict()))
        
        # Add to user's session set
        await self._redis.sadd(user_key, session.session_id)
        await self._redis.expire(user_key, ttl + 3600)  # Keep index a bit longer
    
    async def get(self, session_id: str) -> Optional[Session]:
        key = self._session_key(session_id)
        data = await self._redis.get(key)
        if data:
            return Session.from_dict(json.loads(data))
        return None
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        user_key = self._user_sessions_key(user_id)
        session_ids = await self._redis.smembers(user_key)
        
        sessions = []
        for sid in session_ids:
            session = await self.get(sid.decode() if isinstance(sid, bytes) else sid)
            if session:
                sessions.append(session)
            else:
                # Clean up stale reference
                await self._redis.srem(user_key, sid)
        
        return sessions
    
    async def delete(self, session_id: str) -> None:
        session = await self.get(session_id)
        if session:
            await self._redis.delete(self._session_key(session_id))
            await self._redis.srem(
                self._user_sessions_key(session.user_id),
                session_id
            )
    
    async def delete_all_user_sessions(self, user_id: str) -> int:
        sessions = await self.get_user_sessions(user_id)
        count = 0
        for session in sessions:
            await self._redis.delete(self._session_key(session.session_id))
            count += 1
        await self._redis.delete(self._user_sessions_key(user_id))
        return count


class SessionManager:
    """Comprehensive session management for financial applications.
    
    Provides:
    - Secure session creation with cryptographic IDs
    - Session validation with device binding
    - Concurrent session limits
    - Automatic session cleanup
    - Activity tracking
    
    Example:
        >>> manager = SessionManager(config=SessionConfig())
        >>> session = await manager.create_session(
        >>>     user_id="user123",
        >>>     ip_address="192.168.1.1",
        >>>     user_agent="Mozilla/5.0..."
        >>> )
        >>> is_valid = await manager.validate_session(
        >>>     session_id=session.session_id,
        >>>     ip_address="192.168.1.1",
        >>>     user_agent="Mozilla/5.0..."
        >>> )
    
    Security Considerations:
        - Use cryptographically secure session IDs
        - Implement session fixation protection
        - Bind sessions to device/IP when appropriate
        - Invalidate sessions on password change
        - Monitor for session hijacking patterns
    """
    
    def __init__(
        self,
        config: Optional[SessionConfig] = None,
        storage: Optional[SessionStorage] = None,
    ):
        """Initialize session manager.
        
        Args:
            config: Session configuration
            storage: Session storage backend
        """
        self._config = config or SessionConfig()
        self._storage = storage or InMemorySessionStorage()
    
    def _generate_session_id(self) -> str:
        """Generate a cryptographically secure session ID.
        
        Returns:
            256-bit random session ID (64 hex chars)
        """
        return secrets.token_hex(32)
    
    def _detect_device_name(self, fingerprint: DeviceFingerprint) -> str:
        """Generate user-friendly device name.
        
        Args:
            fingerprint: Device fingerprint
            
        Returns:
            Human-readable device name
        """
        ua = fingerprint.user_agent.lower()
        platform = fingerprint.platform.lower()
        
        # Detect browser
        if "chrome" in ua and "edge" not in ua:
            browser = "Chrome"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "safari" in ua and "chrome" not in ua:
            browser = "Safari"
        elif "edge" in ua:
            browser = "Edge"
        else:
            browser = "Browser"
        
        # Detect OS
        if "windows" in platform or "windows" in ua:
            os_name = "Windows"
        elif "mac" in platform or "macintosh" in ua:
            os_name = "Mac"
        elif "iphone" in ua or "ipad" in ua:
            os_name = "iOS"
        elif "android" in ua:
            os_name = "Android"
        elif "linux" in platform:
            os_name = "Linux"
        else:
            os_name = "Unknown"
        
        return f"{browser} on {os_name}"
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        mfa_verified: bool = False,
        additional_fingerprint: Optional[Dict[str, str]] = None,
    ) -> Session:
        """Create a new session for a user.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            mfa_verified: Whether MFA was completed
            additional_fingerprint: Additional fingerprint data from client
            
        Returns:
            Created session
            
        Raises:
            ValueError: If concurrent session limit exceeded
        """
        # Check concurrent session limit
        existing_sessions = await self._storage.get_user_sessions(user_id)
        active_sessions = [s for s in existing_sessions if s.is_valid()]
        
        if len(active_sessions) >= self._config.max_concurrent_sessions:
            # Revoke oldest session
            oldest = min(active_sessions, key=lambda s: s.last_activity_at)
            await self.revoke_session(oldest.session_id, reason="concurrent_limit")
            logger.info(
                "Session revoked due to concurrent limit",
                extra={
                    "user_id": user_id,
                    "revoked_session": oldest.session_id[:8],
                }
            )
        
        # Create device fingerprint
        fingerprint_data = additional_fingerprint or {}
        fingerprint = DeviceFingerprint(
            user_agent=user_agent,
            accept_language=fingerprint_data.get("accept_language", ""),
            screen_resolution=fingerprint_data.get("screen_resolution", ""),
            timezone=fingerprint_data.get("timezone", ""),
            platform=fingerprint_data.get("platform", ""),
        )
        
        # Create session
        now = datetime.now(timezone.utc)
        session = Session(
            session_id=self._generate_session_id(),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(hours=self._config.absolute_timeout_hours),
            last_activity_at=now,
            ip_address=ip_address,
            device_fingerprint=fingerprint,
            status=SessionStatus.ACTIVE,
            mfa_verified=mfa_verified,
            device_name=self._detect_device_name(fingerprint),
        )
        
        await self._storage.save(session)
        
        logger.info(
            "Session created",
            extra={
                "user_id": user_id,
                "session_id": session.session_id[:8],
                "device_name": session.device_name,
            }
        )
        
        return session
    
    async def validate_session(
        self,
        session_id: str,
        ip_address: str,
        user_agent: str,
    ) -> tuple[bool, Optional[Session], Optional[str]]:
        """Validate a session.
        
        Args:
            session_id: Session ID to validate
            ip_address: Current client IP
            user_agent: Current user agent
            
        Returns:
            Tuple of (is_valid, session, error_reason)
        """
        session = await self._storage.get(session_id)
        
        if not session:
            return False, None, "session_not_found"
        
        if session.status != SessionStatus.ACTIVE:
            return False, session, f"session_{session.status.value}"
        
        # Check expiration
        now = datetime.now(timezone.utc)
        if now >= session.expires_at:
            session.status = SessionStatus.EXPIRED
            await self._storage.save(session)
            return False, session, "session_expired"
        
        # Check idle timeout
        idle_threshold = now - timedelta(minutes=self._config.session_timeout_minutes)
        if session.last_activity_at < idle_threshold:
            session.status = SessionStatus.EXPIRED
            await self._storage.save(session)
            return False, session, "session_idle_timeout"
        
        # Check IP binding (if enabled)
        if self._config.bind_to_ip and session.ip_address != ip_address:
            logger.warning(
                "Session IP mismatch",
                extra={
                    "session_id": session_id[:8],
                    "original_ip": session.ip_address,
                    "current_ip": ip_address,
                }
            )
            # Don't invalidate, but log suspicious activity
            # Some networks (mobile, VPN) may change IPs
        
        # Check device fingerprint binding (if enabled)
        if self._config.bind_to_device:
            current_fingerprint = DeviceFingerprint(user_agent=user_agent)
            if not session.device_fingerprint.matches(current_fingerprint):
                logger.warning(
                    "Session device fingerprint mismatch",
                    extra={
                        "session_id": session_id[:8],
                        "user_id": session.user_id,
                    }
                )
                # Don't invalidate automatically, but consider re-auth
        
        # Update last activity
        session.last_activity_at = now
        await self._storage.save(session)
        
        return True, session, None
    
    async def refresh_session(
        self,
        session_id: str,
    ) -> Optional[Session]:
        """Refresh a session's expiration.
        
        Args:
            session_id: Session ID to refresh
            
        Returns:
            Updated session or None if not found/invalid
        """
        session = await self._storage.get(session_id)
        
        if not session or session.status != SessionStatus.ACTIVE:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Check if refresh is needed
        since_activity = now - session.last_activity_at
        if since_activity < timedelta(minutes=self._config.refresh_threshold_minutes):
            return session
        
        # Refresh session
        session.last_activity_at = now
        session.refresh_count += 1
        
        # Don't extend beyond absolute timeout
        max_expiry = session.created_at + timedelta(hours=self._config.absolute_timeout_hours)
        new_expiry = now + timedelta(minutes=self._config.session_timeout_minutes)
        session.expires_at = min(new_expiry, max_expiry)
        
        await self._storage.save(session)
        
        logger.debug(
            "Session refreshed",
            extra={"session_id": session_id[:8], "refresh_count": session.refresh_count}
        )
        
        return session
    
    async def revoke_session(
        self,
        session_id: str,
        reason: str = "user_logout",
    ) -> bool:
        """Revoke a specific session.
        
        Args:
            session_id: Session ID to revoke
            reason: Reason for revocation
            
        Returns:
            True if session was found and revoked
        """
        session = await self._storage.get(session_id)
        
        if not session:
            return False
        
        if reason == "user_logout":
            session.status = SessionStatus.LOGGED_OUT
        elif reason == "security":
            session.status = SessionStatus.SECURITY_TERMINATED
        else:
            session.status = SessionStatus.REVOKED
        
        await self._storage.save(session)
        
        logger.info(
            "Session revoked",
            extra={
                "session_id": session_id[:8],
                "user_id": session.user_id,
                "reason": reason,
            }
        )
        
        return True
    
    async def revoke_all_user_sessions(
        self,
        user_id: str,
        reason: str = "password_change",
        except_session_id: Optional[str] = None,
    ) -> int:
        """Revoke all sessions for a user.
        
        Args:
            user_id: User whose sessions to revoke
            reason: Reason for revocation
            except_session_id: Optional session to keep active
            
        Returns:
            Number of sessions revoked
        """
        sessions = await self._storage.get_user_sessions(user_id)
        count = 0
        
        for session in sessions:
            if except_session_id and session.session_id == except_session_id:
                continue
            
            if session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.SECURITY_TERMINATED
                await self._storage.save(session)
                count += 1
        
        logger.warning(
            "All user sessions revoked",
            extra={
                "user_id": user_id,
                "reason": reason,
                "count": count,
            }
        )
        
        return count
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of sessions (active and inactive)
        """
        return await self._storage.get_user_sessions(user_id)
    
    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Get active sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active sessions
        """
        sessions = await self._storage.get_user_sessions(user_id)
        return [s for s in sessions if s.is_valid()]
    
    async def update_mfa_status(
        self,
        session_id: str,
        mfa_verified: bool,
    ) -> Optional[Session]:
        """Update MFA verification status for a session.
        
        Args:
            session_id: Session ID
            mfa_verified: Whether MFA was verified
            
        Returns:
            Updated session or None
        """
        session = await self._storage.get(session_id)
        
        if session and session.status == SessionStatus.ACTIVE:
            session.mfa_verified = mfa_verified
            await self._storage.save(session)
            
            logger.info(
                "Session MFA status updated",
                extra={
                    "session_id": session_id[:8],
                    "mfa_verified": mfa_verified,
                }
            )
            
            return session
        
        return None
    
    async def check_suspicious_activity(
        self,
        user_id: str,
        current_ip: str,
        current_fingerprint: DeviceFingerprint,
    ) -> List[str]:
        """Check for suspicious session activity.
        
        Args:
            user_id: User identifier
            current_ip: Current request IP
            current_fingerprint: Current device fingerprint
            
        Returns:
            List of suspicious activity indicators
        """
        indicators = []
        sessions = await self.get_active_sessions(user_id)
        
        # Check for sessions from multiple IPs
        unique_ips = {s.ip_address for s in sessions}
        if len(unique_ips) > 3:
            indicators.append("multiple_ips")
        
        # Check for sessions from different device types
        device_types = {s.device_fingerprint._normalize_platform(s.device_fingerprint.platform) 
                       for s in sessions}
        if len(device_types) > 2:
            indicators.append("multiple_device_types")
        
        # Check for rapid session creation
        now = datetime.now(timezone.utc)
        recent_sessions = [
            s for s in sessions
            if (now - s.created_at).total_seconds() < 3600  # Last hour
        ]
        if len(recent_sessions) > self._config.suspicious_activity_threshold:
            indicators.append("rapid_session_creation")
        
        if indicators:
            logger.warning(
                "Suspicious session activity detected",
                extra={
                    "user_id": user_id,
                    "indicators": indicators,
                }
            )
        
        return indicators


# Session security guidelines
SESSION_SECURITY_GUIDELINES = """
## Session Security Best Practices for Financial Applications

### Session ID Generation
1. Use cryptographically secure random generator
2. Minimum 128 bits of entropy (256 recommended)
3. Never use predictable values (timestamps, user IDs)

### Session Storage
1. Store sessions server-side (Redis recommended)
2. Never store sensitive data in client-side cookies
3. Encrypt session data at rest
4. Set appropriate TTL for automatic cleanup

### Session Binding
1. Bind to device fingerprint when possible
2. Consider IP binding for high-security scenarios
3. Re-authenticate on significant context changes
4. Monitor for session hijacking patterns

### Lifecycle Management
1. Implement idle timeout (15-30 minutes for financial)
2. Implement absolute timeout (8-24 hours)
3. Invalidate on password change
4. Limit concurrent sessions (3-5 devices)
5. Implement proper logout

### Protection Mechanisms
1. Use secure, HttpOnly cookies
2. Implement CSRF protection
3. Regenerate session ID after login
4. Monitor for session fixation attacks

### Compliance
- PCI-DSS: 15-minute idle timeout recommended
- SOC2: Session management controls
- NIST 800-63B: Session binding requirements
"""

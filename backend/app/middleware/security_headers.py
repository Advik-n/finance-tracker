"""
Security Headers Middleware for Finance Tracker

This module provides comprehensive security headers with:
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security
- Content-Security-Policy
- Referrer-Policy
- Permissions-Policy

Security Level: BANK-GRADE
Compliance: OWASP Security Headers, PCI-DSS
"""

import logging
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FrameOptions(Enum):
    """X-Frame-Options values."""
    DENY = "DENY"
    SAMEORIGIN = "SAMEORIGIN"


class ReferrerPolicy(Enum):
    """Referrer-Policy values."""
    NO_REFERRER = "no-referrer"
    NO_REFERRER_WHEN_DOWNGRADE = "no-referrer-when-downgrade"
    SAME_ORIGIN = "same-origin"
    ORIGIN = "origin"
    STRICT_ORIGIN = "strict-origin"
    STRICT_ORIGIN_WHEN_CROSS_ORIGIN = "strict-origin-when-cross-origin"
    ORIGIN_WHEN_CROSS_ORIGIN = "origin-when-cross-origin"
    UNSAFE_URL = "unsafe-url"


class XSSProtection(Enum):
    """X-XSS-Protection values."""
    DISABLED = "0"
    ENABLED = "1"
    ENABLED_BLOCK = "1; mode=block"


@dataclass
class ContentSecurityPolicy:
    """Content Security Policy configuration.
    
    Attributes:
        default_src: Default source for all directives
        script_src: Sources for scripts
        style_src: Sources for stylesheets
        img_src: Sources for images
        font_src: Sources for fonts
        connect_src: Sources for fetch/XHR/WebSocket
        frame_src: Sources for frames
        frame_ancestors: Who can embed this page
        object_src: Sources for plugins
        base_uri: Restrict base URI
        form_action: Restrict form submissions
        upgrade_insecure_requests: Upgrade HTTP to HTTPS
        block_all_mixed_content: Block mixed content
        report_uri: URI for CSP violation reports
        report_to: Reporting API endpoint
    """
    default_src: List[str] = field(default_factory=lambda: ["'self'"])
    script_src: List[str] = field(default_factory=lambda: ["'self'"])
    style_src: List[str] = field(default_factory=lambda: ["'self'"])
    img_src: List[str] = field(default_factory=lambda: ["'self'", "data:"])
    font_src: List[str] = field(default_factory=lambda: ["'self'"])
    connect_src: List[str] = field(default_factory=lambda: ["'self'"])
    frame_src: List[str] = field(default_factory=lambda: ["'none'"])
    frame_ancestors: List[str] = field(default_factory=lambda: ["'none'"])
    object_src: List[str] = field(default_factory=lambda: ["'none'"])
    base_uri: List[str] = field(default_factory=lambda: ["'self'"])
    form_action: List[str] = field(default_factory=lambda: ["'self'"])
    upgrade_insecure_requests: bool = True
    block_all_mixed_content: bool = True
    report_uri: Optional[str] = None
    report_to: Optional[str] = None
    
    def to_header_value(self) -> str:
        """Convert to CSP header value.
        
        Returns:
            CSP header string
        """
        directives = []
        
        # Add source directives
        source_directives = [
            ("default-src", self.default_src),
            ("script-src", self.script_src),
            ("style-src", self.style_src),
            ("img-src", self.img_src),
            ("font-src", self.font_src),
            ("connect-src", self.connect_src),
            ("frame-src", self.frame_src),
            ("frame-ancestors", self.frame_ancestors),
            ("object-src", self.object_src),
            ("base-uri", self.base_uri),
            ("form-action", self.form_action),
        ]
        
        for directive, sources in source_directives:
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
        
        # Add boolean directives
        if self.upgrade_insecure_requests:
            directives.append("upgrade-insecure-requests")
        
        if self.block_all_mixed_content:
            directives.append("block-all-mixed-content")
        
        # Add reporting
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")
        
        if self.report_to:
            directives.append(f"report-to {self.report_to}")
        
        return "; ".join(directives)


@dataclass
class PermissionsPolicy:
    """Permissions Policy (Feature Policy) configuration.
    
    Controls access to browser features.
    """
    accelerometer: List[str] = field(default_factory=list)
    ambient_light_sensor: List[str] = field(default_factory=list)
    autoplay: List[str] = field(default_factory=list)
    battery: List[str] = field(default_factory=list)
    camera: List[str] = field(default_factory=list)
    display_capture: List[str] = field(default_factory=list)
    document_domain: List[str] = field(default_factory=list)
    encrypted_media: List[str] = field(default_factory=list)
    fullscreen: List[str] = field(default_factory=lambda: ["self"])
    geolocation: List[str] = field(default_factory=list)
    gyroscope: List[str] = field(default_factory=list)
    magnetometer: List[str] = field(default_factory=list)
    microphone: List[str] = field(default_factory=list)
    midi: List[str] = field(default_factory=list)
    payment: List[str] = field(default_factory=list)
    picture_in_picture: List[str] = field(default_factory=list)
    usb: List[str] = field(default_factory=list)
    
    def to_header_value(self) -> str:
        """Convert to Permissions-Policy header value.
        
        Returns:
            Permissions-Policy header string
        """
        policies = []
        
        feature_map = {
            "accelerometer": self.accelerometer,
            "ambient-light-sensor": self.ambient_light_sensor,
            "autoplay": self.autoplay,
            "battery": self.battery,
            "camera": self.camera,
            "display-capture": self.display_capture,
            "document-domain": self.document_domain,
            "encrypted-media": self.encrypted_media,
            "fullscreen": self.fullscreen,
            "geolocation": self.geolocation,
            "gyroscope": self.gyroscope,
            "magnetometer": self.magnetometer,
            "microphone": self.microphone,
            "midi": self.midi,
            "payment": self.payment,
            "picture-in-picture": self.picture_in_picture,
            "usb": self.usb,
        }
        
        for feature, allowlist in feature_map.items():
            if not allowlist:
                policies.append(f"{feature}=()")
            else:
                sources = " ".join(allowlist)
                policies.append(f"{feature}=({sources})")
        
        return ", ".join(policies)


@dataclass
class HSTSConfig:
    """HTTP Strict Transport Security configuration.
    
    Attributes:
        max_age: Time in seconds to remember HTTPS only
        include_subdomains: Apply to subdomains
        preload: Allow preload list submission
    """
    max_age: int = 31536000  # 1 year
    include_subdomains: bool = True
    preload: bool = False
    
    def to_header_value(self) -> str:
        """Convert to HSTS header value.
        
        Returns:
            HSTS header string
        """
        value = f"max-age={self.max_age}"
        
        if self.include_subdomains:
            value += "; includeSubDomains"
        
        if self.preload:
            value += "; preload"
        
        return value


@dataclass
class SecurityHeadersConfig:
    """Complete security headers configuration.
    
    Attributes:
        x_content_type_options: Prevent MIME sniffing
        x_frame_options: Clickjacking protection
        x_xss_protection: XSS filter
        referrer_policy: Referrer leakage control
        hsts: HTTPS enforcement
        csp: Content Security Policy
        permissions_policy: Browser feature control
        cache_control: Cache control header
        pragma: Legacy cache control
        x_permitted_cross_domain_policies: Flash/PDF policy
        cross_origin_embedder_policy: COEP
        cross_origin_opener_policy: COOP
        cross_origin_resource_policy: CORP
    """
    x_content_type_options: bool = True
    x_frame_options: FrameOptions = FrameOptions.DENY
    x_xss_protection: XSSProtection = XSSProtection.ENABLED_BLOCK
    referrer_policy: ReferrerPolicy = ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN
    hsts: Optional[HSTSConfig] = field(default_factory=HSTSConfig)
    csp: Optional[ContentSecurityPolicy] = field(default_factory=ContentSecurityPolicy)
    permissions_policy: Optional[PermissionsPolicy] = field(default_factory=PermissionsPolicy)
    cache_control: str = "no-store, no-cache, must-revalidate, private"
    pragma: str = "no-cache"
    x_permitted_cross_domain_policies: str = "none"
    cross_origin_embedder_policy: str = "require-corp"
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "same-origin"


class SecurityHeadersPresets:
    """Predefined security header configurations."""
    
    @staticmethod
    def strict() -> SecurityHeadersConfig:
        """Most restrictive security headers for sensitive financial pages."""
        return SecurityHeadersConfig(
            x_content_type_options=True,
            x_frame_options=FrameOptions.DENY,
            x_xss_protection=XSSProtection.ENABLED_BLOCK,
            referrer_policy=ReferrerPolicy.NO_REFERRER,
            hsts=HSTSConfig(
                max_age=31536000,
                include_subdomains=True,
                preload=True,
            ),
            csp=ContentSecurityPolicy(
                default_src=["'none'"],
                script_src=["'self'"],
                style_src=["'self'"],
                img_src=["'self'"],
                font_src=["'self'"],
                connect_src=["'self'"],
                frame_src=["'none'"],
                frame_ancestors=["'none'"],
                object_src=["'none'"],
                base_uri=["'self'"],
                form_action=["'self'"],
                upgrade_insecure_requests=True,
                block_all_mixed_content=True,
            ),
            permissions_policy=PermissionsPolicy(),
        )
    
    @staticmethod
    def standard() -> SecurityHeadersConfig:
        """Standard security headers for general use."""
        return SecurityHeadersConfig(
            x_content_type_options=True,
            x_frame_options=FrameOptions.SAMEORIGIN,
            x_xss_protection=XSSProtection.ENABLED_BLOCK,
            referrer_policy=ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
            hsts=HSTSConfig(
                max_age=31536000,
                include_subdomains=True,
                preload=False,
            ),
            csp=ContentSecurityPolicy(
                default_src=["'self'"],
                script_src=["'self'", "'unsafe-inline'"],  # May need inline for some frameworks
                style_src=["'self'", "'unsafe-inline'"],
                img_src=["'self'", "data:", "https:"],
                font_src=["'self'", "https://fonts.gstatic.com"],
                connect_src=["'self'"],
                frame_src=["'none'"],
                frame_ancestors=["'self'"],
                object_src=["'none'"],
            ),
        )
    
    @staticmethod
    def api() -> SecurityHeadersConfig:
        """Security headers optimized for API endpoints."""
        return SecurityHeadersConfig(
            x_content_type_options=True,
            x_frame_options=FrameOptions.DENY,
            x_xss_protection=XSSProtection.ENABLED_BLOCK,
            referrer_policy=ReferrerPolicy.NO_REFERRER,
            hsts=HSTSConfig(
                max_age=31536000,
                include_subdomains=True,
            ),
            csp=None,  # CSP less relevant for API responses
            permissions_policy=None,
            cache_control="no-store, no-cache, must-revalidate, private",
        )
    
    @staticmethod
    def static_assets() -> SecurityHeadersConfig:
        """Security headers for static asset responses."""
        return SecurityHeadersConfig(
            x_content_type_options=True,
            x_frame_options=FrameOptions.SAMEORIGIN,
            x_xss_protection=XSSProtection.DISABLED,  # Not needed for static
            referrer_policy=ReferrerPolicy.STRICT_ORIGIN,
            hsts=HSTSConfig(),
            csp=None,
            cache_control="public, max-age=31536000, immutable",
        )


class SecurityHeadersMiddleware:
    """ASGI middleware for security headers.
    
    Adds comprehensive security headers to all responses.
    
    Example:
        >>> config = SecurityHeadersPresets.strict()
        >>> app = FastAPI()
        >>> app.add_middleware(SecurityHeadersMiddleware, config=config)
    
    Security Considerations:
        - Test CSP thoroughly before deployment
        - Monitor CSP violation reports
        - Update headers as browser support changes
        - Different pages may need different headers
    """
    
    # Paths that should skip certain headers (e.g., CSP for specific endpoints)
    SKIP_CSP_PATHS: Set[str] = set()
    
    # Paths that need different caching
    STATIC_PATHS: Set[str] = {"/static/", "/assets/", "/favicon.ico"}
    
    def __init__(
        self,
        app,
        config: Optional[SecurityHeadersConfig] = None,
        enforce_https: bool = True,
    ):
        """Initialize security headers middleware.
        
        Args:
            app: ASGI application
            config: Security headers configuration
            enforce_https: Only add HSTS in HTTPS context
        """
        self.app = app
        self.config = config or SecurityHeadersPresets.strict()
        self.enforce_https = enforce_https
        
        # Pre-compute static headers
        self._headers = self._build_headers()
    
    def _build_headers(self) -> List[tuple]:
        """Build static header list from configuration.
        
        Returns:
            List of (name, value) tuples
        """
        headers = []
        
        # X-Content-Type-Options
        if self.config.x_content_type_options:
            headers.append((b"x-content-type-options", b"nosniff"))
        
        # X-Frame-Options
        if self.config.x_frame_options:
            headers.append(
                (b"x-frame-options", self.config.x_frame_options.value.encode())
            )
        
        # X-XSS-Protection
        if self.config.x_xss_protection:
            headers.append(
                (b"x-xss-protection", self.config.x_xss_protection.value.encode())
            )
        
        # Referrer-Policy
        if self.config.referrer_policy:
            headers.append(
                (b"referrer-policy", self.config.referrer_policy.value.encode())
            )
        
        # Content-Security-Policy
        if self.config.csp:
            headers.append(
                (b"content-security-policy", self.config.csp.to_header_value().encode())
            )
        
        # Permissions-Policy
        if self.config.permissions_policy:
            headers.append(
                (b"permissions-policy", self.config.permissions_policy.to_header_value().encode())
            )
        
        # Cache-Control
        if self.config.cache_control:
            headers.append((b"cache-control", self.config.cache_control.encode()))
        
        # Pragma
        if self.config.pragma:
            headers.append((b"pragma", self.config.pragma.encode()))
        
        # X-Permitted-Cross-Domain-Policies
        if self.config.x_permitted_cross_domain_policies:
            headers.append(
                (b"x-permitted-cross-domain-policies", 
                 self.config.x_permitted_cross_domain_policies.encode())
            )
        
        # Cross-Origin headers
        if self.config.cross_origin_embedder_policy:
            headers.append(
                (b"cross-origin-embedder-policy",
                 self.config.cross_origin_embedder_policy.encode())
            )
        
        if self.config.cross_origin_opener_policy:
            headers.append(
                (b"cross-origin-opener-policy",
                 self.config.cross_origin_opener_policy.encode())
            )
        
        if self.config.cross_origin_resource_policy:
            headers.append(
                (b"cross-origin-resource-policy",
                 self.config.cross_origin_resource_policy.encode())
            )
        
        return headers
    
    def _get_headers_for_path(self, path: str, is_https: bool) -> List[tuple]:
        """Get appropriate headers for a specific path.
        
        Args:
            path: Request path
            is_https: Whether request is over HTTPS
            
        Returns:
            List of headers to add
        """
        headers = list(self._headers)
        
        # Add HSTS only for HTTPS
        if is_https and self.config.hsts:
            headers.append(
                (b"strict-transport-security", self.config.hsts.to_header_value().encode())
            )
        
        # Modify cache-control for static assets
        for static_path in self.STATIC_PATHS:
            if path.startswith(static_path):
                headers = [h for h in headers if h[0] != b"cache-control"]
                headers.append(
                    (b"cache-control", b"public, max-age=31536000, immutable")
                )
                break
        
        return headers
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "/")
        
        # Determine if HTTPS
        is_https = scope.get("scheme") == "https"
        
        # Check for X-Forwarded-Proto header (behind proxy)
        headers = dict(scope.get("headers", []))
        forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode()
        if forwarded_proto == "https":
            is_https = True
        
        # Get headers for this path
        security_headers = self._get_headers_for_path(path, is_https)
        
        # Wrap send to add security headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Get existing headers
                existing_headers = list(message.get("headers", []))
                
                # Add security headers (don't override if already set)
                existing_names = {h[0] for h in existing_headers}
                for name, value in security_headers:
                    if name not in existing_names:
                        existing_headers.append((name, value))
                
                message["headers"] = existing_headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class SecurityHeadersValidator:
    """Validate security headers configuration."""
    
    @staticmethod
    def validate(config: SecurityHeadersConfig) -> List[str]:
        """Validate security headers configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of warnings/issues
        """
        issues = []
        
        # Check for missing critical headers
        if not config.x_content_type_options:
            issues.append("WARNING: X-Content-Type-Options is disabled")
        
        if not config.x_frame_options:
            issues.append("WARNING: X-Frame-Options is not set")
        
        if not config.hsts:
            issues.append("WARNING: HSTS is not configured")
        elif config.hsts.max_age < 31536000:
            issues.append("WARNING: HSTS max-age is less than 1 year")
        
        # Check CSP
        if config.csp:
            csp_issues = SecurityHeadersValidator._validate_csp(config.csp)
            issues.extend(csp_issues)
        else:
            issues.append("INFO: Content-Security-Policy is not configured")
        
        # Check referrer policy
        if config.referrer_policy == ReferrerPolicy.UNSAFE_URL:
            issues.append("WARNING: Referrer-Policy unsafe-url leaks full URL")
        
        return issues
    
    @staticmethod
    def _validate_csp(csp: ContentSecurityPolicy) -> List[str]:
        """Validate CSP configuration.
        
        Args:
            csp: CSP configuration
            
        Returns:
            List of CSP-specific issues
        """
        issues = []
        
        # Check for unsafe inline
        if "'unsafe-inline'" in csp.script_src:
            issues.append(
                "WARNING: CSP script-src allows 'unsafe-inline'. "
                "This significantly reduces XSS protection."
            )
        
        if "'unsafe-eval'" in csp.script_src:
            issues.append(
                "WARNING: CSP script-src allows 'unsafe-eval'. "
                "This allows eval() and similar functions."
            )
        
        # Check for wildcard
        if "*" in csp.default_src or "*" in csp.script_src:
            issues.append(
                "CRITICAL: CSP contains wildcard (*) in source. "
                "This provides minimal protection."
            )
        
        # Check frame-ancestors
        if "'none'" not in csp.frame_ancestors and "self" not in str(csp.frame_ancestors):
            issues.append(
                "INFO: Consider setting frame-ancestors to prevent clickjacking."
            )
        
        # Check object-src
        if "'none'" not in csp.object_src:
            issues.append(
                "WARNING: object-src should be 'none' to prevent plugin-based attacks."
            )
        
        return issues


# Security headers guidelines
SECURITY_HEADERS_GUIDELINES = """
## Security Headers Best Practices for Financial Applications

### Essential Headers
1. **X-Content-Type-Options: nosniff**
   - Prevents MIME sniffing attacks
   - Always enable

2. **X-Frame-Options: DENY**
   - Prevents clickjacking
   - Use DENY for most pages

3. **Strict-Transport-Security**
   - Enforce HTTPS
   - Use max-age of at least 1 year
   - Include subdomains
   - Consider HSTS preload

4. **Content-Security-Policy**
   - Prevent XSS attacks
   - Start with strict policy
   - Test thoroughly before deployment
   - Monitor violation reports

5. **Referrer-Policy: strict-origin-when-cross-origin**
   - Prevent referrer leakage
   - Use no-referrer for sensitive pages

### Recommended Values
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
Permissions-Policy: geolocation=(), camera=(), microphone=()
```

### Testing
1. Use security header checkers (securityheaders.com)
2. Test CSP in report-only mode first
3. Verify no functionality is broken
4. Monitor CSP violation reports

### Compliance
- OWASP: Security headers requirement
- PCI-DSS: Protect cardholder data
- SOC2: Access control
"""

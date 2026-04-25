# Integration Architecture

## User Management Portal — API Gateway, Auth Flow, and External Integrations

---

## 1. API Gateway Design

### 1.1 API Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                 │
└─────────────────────────────────────────────────────────────────────────────┘

     Client Request
          │
          ▼
┌─────────────────────┐
│   Azure Front Door  │  • Global load balancing
│   (Optional CDN)    │  • DDoS protection
│                     │  • SSL termination
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Azure App Service │  • Web Application Firewall (WAF)
│   (Nginx + FastAPI) │  • Rate limiting
│                     │  • Request routing
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST PROCESSING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Security Layer                                                          │
│     ├── HTTPS enforcement (TLS 1.3)                                         │
│     ├── CORS validation                                                     │
│     ├── Security headers (HSTS, CSP, X-Frame-Options)                       │
│     └── IP allowlisting (optional)                                          │
│                                                                             │
│  2. Authentication Layer                                                    │
│     ├── JWT token extraction (Bearer)                                       │
│     ├── Token validation (signature, expiry)                                │
│     └── Claims extraction (user_id, role, permissions)                      │
│                                                                             │
│  3. Rate Limiting Layer                                                     │
│     ├── Global rate limit: 100 req/min per IP                             │
│     ├── Auth endpoints: 5 req/min per IP (login/signup)                     │
│     ├── API endpoints: 1000 req/min per user                                │
│     └── Burst handling with token bucket algorithm                          │
│                                                                             │
│  4. Routing Layer                                                           │
│     ├── /api/v1/auth/* → AuthController                                     │
│     ├── /api/v1/users/* → UserController                                    │
│     ├── /api/health → HealthController                                      │
│     └── /api/docs → Swagger UI (dev only)                                   │
│                                                                             │
│  5. Validation Layer                                                        │
│     ├── Request body validation (Pydantic)                                  │
│     ├── Query parameter validation                                          │
│     └── Content-Type enforcement                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 API Versioning Strategy

```
API Versioning: URL Path-based

Current Version: v1
Base URL: https://api.usermgmt.example.com/api/v1

Versioning Rules:
- Major versions in URL: /api/v1/, /api/v2/
- Minor versions in Accept header: Accept: application/vnd.api+json;version=1.1
- Deprecation: 6 months notice via Sunset header
- Breaking changes → new major version
- Non-breaking changes → same version

Examples:
GET  /api/v1/users           # List users (v1)
GET  /api/v2/users           # List users (v2 - breaking changes)
POST /api/v1/auth/login      # Login (v1)
```

### 1.3 Rate Limiting Configuration

```python
# core/rate_limit.py
from fastapi import Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

from app.core.config import settings
from app.core.cache import CacheKeys

# Redis-based rate limiting
async def init_rate_limiter():
    redis_connection = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


class RateLimitConfig:
    """Rate limiting configurations."""
    
    # Strict limits for authentication endpoints
    AUTH = RateLimiter(times=5, seconds=60)  # 5 requests per minute
    
    # Standard limits for API endpoints
    STANDARD = RateLimiter(times=100, seconds=60)  # 100 requests per minute
    
    # Relaxed limits for read-only endpoints
    READ_ONLY = RateLimiter(times=200, seconds=60)  # 200 requests per minute


async def custom_identifier(request: Request) -> str:
    """Generate unique identifier for rate limiting."""
    # Use user ID if authenticated, otherwise IP address
    user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
    if user_id:
        return f"user:{user_id}"
    
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    
    return f"ip:{request.client.host}"


# Usage in routes
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/login", dependencies=[Depends(RateLimitConfig.AUTH)])
async def login(credentials: LoginRequest):
    """Login endpoint with strict rate limiting."""
    pass

@router.get("/users", dependencies=[Depends(RateLimitConfig.READ_ONLY)])
async def list_users():
    """List users with relaxed rate limiting."""
    pass
```

---

## 2. JWT Authentication Flow

### 2.1 Token Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JWT TOKEN ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

Token Types:
┌─────────────────────┐    ┌─────────────────────┐
│   Access Token      │    │   Refresh Token     │
├─────────────────────┤    ├─────────────────────┤
│ • JWT format        │    │ • JWT format        │
│ • Short-lived       │    │ • Long-lived        │
│ • Contains claims   │    │ • Single use        │
│ • Stateless         │    │ • Stored in DB      │
│ • 15 minutes TTL    │    │ • 7 days TTL        │
└─────────────────────┘    └─────────────────────┘

Token Claims (Access):
{
  "sub": "user-uuid",           // Subject (user ID)
  "email": "user@example.com",  // User email
  "role": "admin",              // User role
  "permissions": ["read", "write"],
  "iat": 1706198400,           // Issued at
  "exp": 1706199300,           // Expiration (15 min)
  "jti": "unique-token-id",    // JWT ID (for revocation)
  "iss": "ump-api",            // Issuer
  "aud": "ump-client"          // Audience
}

Token Claims (Refresh):
{
  "sub": "user-uuid",
  "jti": "unique-refresh-id",
  "iat": 1706198400,
  "exp": 1706803200,           // 7 days
  "type": "refresh"
}
```

### 2.2 Authentication Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JWT AUTHENTICATION SEQUENCE                              │
└─────────────────────────────────────────────────────────────────────────────┘

     Client          API Gateway          Auth Service         Database
       │                  │                     │                  │
       │ 1. POST /login   │                     │                  │
       │ {email, pass}    │                     │                  │
       │─────────────────►│                     │                  │
       │                  │                     │                  │
       │                  │ 2. Forward request  │                  │
       │                  │────────────────────►│                  │
       │                  │                     │                  │
       │                  │                     │ 3. Validate creds│
       │                  │                     │─────────────────►│
       │                  │                     │◄─────────────────│
       │                  │                     │                  │
       │                  │                     │ 4. Generate      │
       │                  │                     │    token pair    │
       │                  │                     │                  │
       │                  │                     │ 5. Store refresh │
       │                  │                     │    token hash    │
       │                  │                     │─────────────────►│
       │                  │                     │◄─────────────────│
       │                  │                     │                  │
       │                  │◄────────────────────│ 6. Return tokens │
       │                  │                     │                  │
       │ 7. Set cookies   │                     │                  │
       │ {access, refresh}│                     │                  │
       │◄─────────────────│                     │                  │
       │                  │                     │                  │
       │ ═══════════════════════════════════════════════════════════
       │                  SUBSEQUENT REQUESTS
       │ ═══════════════════════════════════════════════════════════
       │                  │                     │                  │
       │ 8. GET /users    │                     │                  │
       │ Authorization:   │                     │                  │
       │ Bearer <access>  │                     │                  │
       │─────────────────►│                     │                  │
       │                  │                     │                  │
       │                  │ 9. Validate JWT     │                  │
       │                  │ (signature, exp)    │                  │
       │                  │                     │                  │
       │                  │ 10. Extract claims  │                  │
       │                  │ (sub, role, perm)   │                  │
       │                  │                     │                  │
       │                  │ 11. Check RBAC      │                  │
       │                  │                     │                  │
       │                  │ 12. Forward to      │                  │
       │                  │     handler         │                  │
       │                  │                     │                  │
       │ 13. Response     │                     │                  │
       │◄─────────────────│                     │                  │
       │                  │                     │                  │
       │ ═══════════════════════════════════════════════════════════
       │                  TOKEN REFRESH (access expired)
       │ ═══════════════════════════════════════════════════════════
       │                  │                     │                  │
       │ 14. POST /refresh│                     │                  │
       │ {refresh_token}  │                     │                  │
       │─────────────────►│                     │                  │
       │                  │                     │                  │
       │                  │ 15. Validate        │                  │
       │                  │     refresh token   │                  │
       │                  │────────────────────►│                  │
       │                  │                     │                  │
       │                  │                     │ 16. Check DB     │
       │                  │                     │     for token    │
       │                  │                     │─────────────────►│
       │                  │                     │◄─────────────────│
       │                  │                     │                  │
       │                  │                     │ 17. Rotate token │
       │                  │                     │ (revoke old,     │
       │                  │                     │  create new)     │
       │                  │                     │                  │
       │                  │◄────────────────────│ 18. New tokens   │
       │                  │                     │                  │
       │ 19. New cookies  │                     │                  │
       │◄─────────────────│                     │                  │
       │                  │                     │                  │
```

### 2.3 JWT Implementation

```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=65536,
    argon2__parallelism=4
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


class JWTManager:
    """JWT token management."""
    
    ALGORITHM = "HS256"
    
    @classmethod
    def create_access_token(
        cls,
        user_id: str,
        email: str,
        role: str,
        permissions: list,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid4()),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access"
        }
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=cls.ALGORITHM
        )
    
    @classmethod
    def create_refresh_token(
        cls,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, str]:
        """Create a new refresh token. Returns (token, jti)."""
        jti = str(uuid4())
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode = {
            "sub": user_id,
            "jti": jti,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        token = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=cls.ALGORITHM
        )
        
        return token, jti
    
    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[cls.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
    
    @classmethod
    def decode_token_unverified(cls, token: str) -> Dict[str, Any]:
        """Decode token without verification (for getting jti)."""
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
```

### 2.4 FastAPI JWT Dependency

```python
# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import JWTManager
from app.core.cache import redis_client, CacheKeys
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenPayload

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = JWTManager.decode_token(token)
        token_data = TokenPayload(**payload)
        
        # Check if token is revoked
        jti = payload.get("jti")
        if jti:
            is_revoked = await redis_client.get(f"revoked_token:{jti}")
            if is_revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token_data.sub)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency for superuser-only endpoints."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


class RoleChecker:
    """Dependency factory for role-based access control."""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {self.allowed_roles}"
            )
        return user


# Role-based dependencies
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_user = RoleChecker(["admin", "manager", "user"])
```

---

## 3. External Service Integrations

### 3.1 Integration Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICE INTEGRATIONS                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          CURRENT INTEGRATIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐     │
│  │  Azure Monitor│         │  Azure AD     │         │  SendGrid     │     │
│  │  (Optional)   │         │  (Optional)   │         │  (Optional)   │     │
│  │               │         │               │         │               │     │
│  │ • Logging     │         │ • SSO         │         │ • Email       │     │
│  │ • Metrics     │         │ • SAML/OIDC   │         │ • Password    │     │
│  │ • Alerts      │         │               │         │   reset       │     │
│  └───────────────┘         └───────────────┘         └───────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Integration Patterns:
├── Sync (Request/Response): Azure AD login flow
├── Async (Event-driven): Audit log streaming
├── Webhook: External system notifications
└── Polling: Status checks
```

### 3.2 Azure Monitor Integration

```python
# core/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.azure.monitor import AzureMonitorTraceExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import logging
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from app.core.config import settings


def setup_telemetry(app):
    """Configure Azure Application Insights telemetry."""
    
    if not settings.APPINSIGHTS_CONNECTION_STRING:
        return
    
    # Tracing
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()
    
    exporter = AzureMonitorTraceExporter(
        connection_string=settings.APPINSIGHTS_CONNECTION_STRING
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Logging
    logger_provider = LoggerProvider()
    log_exporter = AzureMonitorLogExporter(
        connection_string=settings.APPINSIGHTS_CONNECTION_STRING
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    
    # Attach to root logger
    handler = LoggingHandler(logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


# Custom telemetry
tracer = trace.get_tracer(__name__)

async def track_user_login(user_id: str, success: bool, ip_address: str):
    """Track user login events."""
    with tracer.start_as_current_span("user_login") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("login.success", success)
        span.set_attribute("client.ip", ip_address)
```

### 3.3 Email Service Integration (SendGrid)

```python
# services/email.py
from typing import Optional
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.core.config import settings


class EmailService:
    """Email service using SendGrid."""
    
    def __init__(self):
        self.client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = Email(settings.FROM_EMAIL)
    
    async def send_password_reset(
        self,
        to_email: str,
        reset_token: str,
        user_name: str
    ) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        mail = Mail(
            from_email=self.from_email,
            to_emails=To(to_email),
            subject="Password Reset Request",
            html_content=Content(
                "text/html",
                f"""
                <h2>Password Reset</h2>
                <p>Hello {user_name},</p>
                <p>You requested a password reset. Click the link below:</p>
                <a href="{reset_url}">Reset Password</a>
                <p>This link expires in 24 hours.</p>
                """
            )
        )
        
        try:
            response = self.client.send(mail)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """Send welcome email to new users."""
        mail = Mail(
            from_email=self.from_email,
            to_emails=To(to_email),
            subject="Welcome to User Management Portal",
            html_content=Content(
                "text/html",
                f"""
                <h2>Welcome!</h2>
                <p>Hello {user_name},</p>
                <p>Your account has been created successfully.</p>
                """
            )
        )
        
        try:
            response = self.client.send(mail)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
```

---

## 4. Security Headers & CORS

### 4.1 Security Middleware

```python
# middleware/security.py
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.usermgmt.example.com;"
        )
        
        # HSTS (HTTPS only)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


def setup_security_middleware(app):
    """Configure all security middleware."""
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"],
        max_age=600,
    )
    
    # Trusted hosts (production only)
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
```

---

## 5. API Documentation

### 5.1 OpenAPI Specification

```yaml
# openapi.yaml (excerpt)
openapi: 3.0.3
info:
  title: User Management Portal API
  version: 1.0.0
  description: |
    API for user management with JWT authentication.
    
servers:
  - url: https://api.usermgmt.example.com/api/v1
    description: Production
  - url: https://api-staging.usermgmt.example.com/api/v1
    description: Staging

security:
  - bearerAuth: []

paths:
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login
      security: []  # No auth required
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        401:
          description: Invalid credentials
          
  /users:
    get:
      tags: [Users]
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: search
          in: query
          schema:
            type: string
        - name: role
          in: query
          schema:
            type: string
            enum: [admin, manager, user, viewer]
        - name: is_active
          in: query
          schema:
            type: boolean
      responses:
        200:
          description: List of users
          headers:
            X-Total-Count:
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-25  
**Owner**: System Architect

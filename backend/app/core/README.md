# Backend Core Module

Core application modules for the User Management Portal.

## Structure

```
core/
├── __init__.py          # Package initialization
├── config.py            # Application configuration (Pydantic Settings)
├── security.py          # JWT, password hashing, RBAC
├── logging.py           # Structured logging configuration
└── exceptions.py        # Custom exception classes
```

## Configuration

Environment variables are loaded from `.env` file and validated using Pydantic Settings.

Required variables:
- `SECRET_KEY`: JWT signing key (min 32 chars)
- `DATABASE_URL`: PostgreSQL connection URL

Optional variables:
- `DEBUG`: Enable debug mode (default: False)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT expiry (default: 15)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiry (default: 7)

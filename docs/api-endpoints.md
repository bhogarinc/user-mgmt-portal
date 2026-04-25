# API Endpoint Catalog

## User Management Portal API v1.0.0

Base URL: `https://api.usermgmt.example.com/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Password Management](#password-management)
3. [User Profile](#user-profile)
4. [Admin User Management](#admin-user-management)
5. [Role Management](#role-management)
6. [Session Management](#session-management)
7. [Audit Logging](#audit-logging)
8. [System](#system)

---

## Authentication

### POST /auth/register
Register a new user account with email verification.

**Rate Limit:** 5 requests/minute

#### Request
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-0123"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "message": "User registered successfully. Please check your email for verification.",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "status": "pending_verification",
    "verification_token_expires": "2024-01-15T12:00:00Z"
  }
}
```

#### Error Responses
- `400` - Invalid request data
- `409` - Email already registered
- `422` - Validation error (weak password, invalid email)

---

### POST /auth/verify-email
Verify user's email address using the token sent via email.

#### Request
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Email verified successfully. You can now log in."
}
```

---

### POST /auth/login
Authenticate user and receive JWT tokens.

**Rate Limit:** 5 requests/minute

#### Request
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "remember_me": true
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "User",
      "is_email_verified": true
    }
  }
}
```

**Token Details:**
- Access Token: 15 minutes expiry
- Refresh Token: 7 days (30 days if remember_me=true)

---

### POST /auth/refresh
Get a new access token using a valid refresh token.

#### Request
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

---

### POST /auth/logout
Invalidate current tokens and end session.

**Authentication Required:** Yes

#### Request
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### GET /auth/me
Get information about the currently authenticated user.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0123",
    "avatar_url": "https://cdn.example.com/avatars/550e8400.jpg",
    "role": "User",
    "permissions": ["user:read", "user:update"],
    "is_email_verified": true,
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z",
    "last_login_at": "2024-01-15T08:30:00Z"
  }
}
```

---

## Password Management

### POST /auth/forgot-password
Request password reset email.

**Rate Limit:** 3 requests/hour

#### Request
```json
{
  "email": "john.doe@example.com"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent."
}
```

---

### POST /auth/reset-password
Reset password using token from email.

#### Request
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123!"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

---

### POST /auth/change-password
Change password while authenticated.

**Authentication Required:** Yes

#### Request
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewSecurePass123!"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## User Profile

### GET /users/profile
Get detailed profile information.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0123",
    "avatar_url": "https://cdn.example.com/avatars/550e8400.jpg",
    "timezone": "America/New_York",
    "language": "en",
    "preferences": {
      "email_notifications": true,
      "two_factor_enabled": false
    }
  }
}
```

---

### PUT /users/profile
Update profile information.

**Authentication Required:** Yes

#### Request
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-0124",
  "timezone": "America/Los_Angeles",
  "language": "en"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0124",
    "timezone": "America/Los_Angeles",
    "language": "en"
  }
}
```

---

### POST /users/profile/avatar
Upload avatar image.

**Authentication Required:** Yes
**Content-Type:** `multipart/form-data`

#### Request
```
POST /users/profile/avatar
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="avatar.jpg"
Content-Type: image/jpeg

[binary data]
------WebKitFormBoundary--
```

**Constraints:**
- Max file size: 5MB
- Allowed formats: JPEG, PNG
- Recommended dimensions: 400x400px

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "avatar_url": "https://cdn.example.com/avatars/550e8400.jpg?v=1705312800"
  }
}
```

---

### DELETE /users/profile/avatar
Remove avatar and revert to default.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Avatar removed successfully"
}
```

---

## Admin User Management

### GET /admin/users
List all users with filtering and pagination.

**Authentication Required:** Yes (Admin/Manager)
**Rate Limit:** 200 requests/minute

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| page_size | integer | Items per page (default: 20, max: 100) |
| search | string | Search by name or email |
| role | string | Filter by role (Admin, Manager, User) |
| status | string | Filter by status (active, inactive, pending_verification, suspended) |
| is_email_verified | boolean | Filter by verification status |
| created_from | date | Filter users created after |
| created_to | date | Filter users created before |
| sort_by | string | Sort field (default: created_at) |
| sort_order | string | Sort direction (asc, desc) |

#### Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "User",
      "is_email_verified": true,
      "is_active": true,
      "last_login_at": "2024-01-15T08:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 156,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

---

### POST /admin/users
Create a new user (Admin function).

**Authentication Required:** Yes (Admin/Manager)

#### Request
```json
{
  "email": "newuser@example.com",
  "password": "TempPass123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "User",
  "phone": "+1-555-0199",
  "is_email_verified": true,
  "is_active": true
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "User",
    "is_email_verified": true,
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### GET /admin/users/{user_id}
Get detailed information about a specific user.

**Authentication Required:** Yes (Admin/Manager)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0123",
    "avatar_url": "https://cdn.example.com/avatars/550e8400.jpg",
    "role": "User",
    "permissions": ["user:read", "user:update"],
    "is_email_verified": true,
    "is_active": true,
    "timezone": "America/New_York",
    "language": "en",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T08:30:00Z",
    "last_login_at": "2024-01-15T08:30:00Z",
    "login_count": 45
  }
}
```

---

### PUT /admin/users/{user_id}
Update user information.

**Authentication Required:** Yes (Admin/Manager)

#### Request
```json
{
  "first_name": "John",
  "last_name": "Doe-Updated",
  "phone": "+1-555-0125",
  "role": "Manager",
  "is_active": true
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe-Updated",
    "role": "Manager",
    "is_active": true,
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

---

### DELETE /admin/users/{user_id}
Delete a user account.

**Authentication Required:** Yes (Admin only)

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| permanent | boolean | false | Permanently delete (cannot be undone) |

#### Response (200 OK)
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

---

### PATCH /admin/users/{user_id}/status
Update user account status.

**Authentication Required:** Yes (Admin/Manager)

#### Request
```json
{
  "status": "suspended",
  "reason": "Violation of terms of service"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "is_active": false,
    "status": "suspended"
  }
}
```

---

### PATCH /admin/users/{user_id}/role
Update user role.

**Authentication Required:** Yes (Admin only)

#### Request
```json
{
  "role": "Manager"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "role": "Manager",
    "permissions": ["user:read", "user:update", "user:list", "user:create"]
  }
}
```

---

### POST /admin/users/bulk
Perform bulk operations on multiple users.

**Authentication Required:** Yes (Admin only)

#### Request
```json
{
  "operation": "change_role",
  "user_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "role": "Manager"
}
```

**Operations:** `activate`, `deactivate`, `delete`, `change_role`

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "processed": 3,
    "succeeded": 3,
    "failed": 0,
    "errors": []
  }
}
```

---

## Role Management

### GET /roles
List all roles with permissions.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "role_id": "110e8400-e29b-41d4-a716-446655440000",
      "name": "Admin",
      "description": "Full system access",
      "permissions": [
        {
          "permission_id": "p001",
          "name": "user:read",
          "resource": "user",
          "action": "read"
        },
        {
          "permission_id": "p002",
          "name": "user:create",
          "resource": "user",
          "action": "create"
        },
        {
          "permission_id": "p003",
          "name": "user:update",
          "resource": "user",
          "action": "update"
        },
        {
          "permission_id": "p004",
          "name": "user:delete",
          "resource": "user",
          "action": "delete"
        }
      ],
      "user_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "role_id": "220e8400-e29b-41d4-a716-446655440000",
      "name": "Manager",
      "description": "User management access",
      "permissions": [
        {
          "permission_id": "p001",
          "name": "user:read",
          "resource": "user",
          "action": "read"
        },
        {
          "permission_id": "p002",
          "name": "user:create",
          "resource": "user",
          "action": "create"
        }
      ],
      "user_count": 12,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "role_id": "330e8400-e29b-41d4-a716-446655440000",
      "name": "User",
      "description": "Standard user access",
      "permissions": [
        {
          "permission_id": "p001",
          "name": "user:read",
          "resource": "user",
          "action": "read"
        },
        {
          "permission_id": "p005",
          "name": "user:update_own",
          "resource": "user",
          "action": "update_own"
        }
      ],
      "user_count": 145,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET /roles/{role_id}
Get role details.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "role_id": "110e8400-e29b-41d4-a716-446655440000",
    "name": "Admin",
    "description": "Full system access",
    "permissions": [...],
    "user_count": 5
  }
}
```

---

### PUT /roles/{role_id}/permissions
Update role permissions (Admin only).

**Authentication Required:** Yes (Admin only)

#### Request
```json
{
  "permissions": [
    "user:read",
    "user:create",
    "user:update",
    "session:read"
  ]
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "role_id": "220e8400-e29b-41d4-a716-446655440000",
    "name": "Manager",
    "permissions": [...]
  }
}
```

---

## Session Management

### GET /sessions
List all active sessions for current user.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "session_id": "990e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "location": "New York, USA",
      "created_at": "2024-01-15T08:30:00Z",
      "last_activity_at": "2024-01-15T14:45:00Z",
      "expires_at": "2024-01-22T08:30:00Z",
      "is_current": true
    },
    {
      "session_id": "880e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "ip_address": "192.168.1.105",
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
      "location": "New York, USA",
      "created_at": "2024-01-14T18:20:00Z",
      "last_activity_at": "2024-01-15T10:15:00Z",
      "expires_at": "2024-01-21T18:20:00Z",
      "is_current": false
    }
  ]
}
```

---

### DELETE /sessions/{session_id}
Revoke a specific session.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Session revoked successfully"
}
```

---

### DELETE /sessions/revoke-all
Revoke all sessions except current one.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "message": "All other sessions revoked successfully"
}
```

---

### GET /admin/sessions
List all active sessions (Admin only).

**Authentication Required:** Yes (Admin only)

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| page_size | integer | Items per page |
| user_id | string | Filter by user ID |

#### Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "session_id": "990e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "john.doe@example.com",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "location": "New York, USA",
      "created_at": "2024-01-15T08:30:00Z",
      "last_activity_at": "2024-01-15T14:45:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 42
  }
}
```

---

## Audit Logging

### GET /audit/logs
Get audit logs with filtering.

**Authentication Required:** Yes

- Regular users: Can only see their own logs
- Admin/Manager: Can see all logs

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| page_size | integer | Items per page |
| user_id | string | Filter by user (Admin only) |
| action | string | Filter by action type |
| resource_type | string | Filter by resource |
| from_date | datetime | Start date |
| to_date | datetime | End date |
| ip_address | string | Filter by IP |

#### Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "log_id": "770e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "john.doe@example.com",
      "action": "login",
      "resource_type": "authentication",
      "resource_id": null,
      "details": {
        "method": "password",
        "mfa_used": false
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "created_at": "2024-01-15T08:30:00Z"
    },
    {
      "log_id": "660e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "john.doe@example.com",
      "action": "update",
      "resource_type": "profile",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000",
      "details": {
        "fields_changed": ["phone", "timezone"]
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "created_at": "2024-01-15T10:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 128
  }
}
```

---

### GET /audit/logs/{log_id}
Get specific audit log details.

**Authentication Required:** Yes

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "log_id": "770e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_email": "john.doe@example.com",
    "action": "login",
    "resource_type": "authentication",
    "details": {...},
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "success": true,
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### GET /admin/audit/export
Export audit logs (Admin only).

**Authentication Required:** Yes (Admin only)

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| format | string | csv | Export format (csv, json) |
| from_date | datetime | - | Start date |
| to_date | datetime | - | End date |

#### Response (200 OK)
**CSV Format:**
```csv
log_id,user_id,action,resource_type,created_at
770e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440000,login,authentication,2024-01-15T08:30:00Z
```

**JSON Format:**
```json
[
  {
    "log_id": "770e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "login",
    "resource_type": "authentication",
    "created_at": "2024-01-15T08:30:00Z"
  }
]
```

---

## System

### GET /health
Health check endpoint.

**Authentication:** None required

#### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:45:00Z",
  "version": "1.0.0",
  "services": {
    "database": "up",
    "cache": "up"
  }
}
```

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Refresh Flow

1. Access tokens expire after 15 minutes
2. Use refresh token to get new access token
3. Refresh tokens expire after 7 days (30 days with remember_me)

```javascript
// Example token refresh
const response = await fetch('/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token: storedRefreshToken })
});

const { data } = await response.json();
localStorage.setItem('access_token', data.access_token);
```

---

## Rate Limiting

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Authentication (login, register) | 5 | per minute |
| Password reset | 3 | per hour |
| General API | 100 | per minute |
| Admin endpoints | 200 | per minute |
| File uploads | 10 | per minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| BAD_REQUEST | 400 | Invalid request parameters |
| VALIDATION_ERROR | 422 | Request validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| TOKEN_EXPIRED | 410 | Token has expired |
| ACCOUNT_DISABLED | 403 | Account is disabled |
| EMAIL_NOT_VERIFIED | 403 | Email not verified |
| INTERNAL_ERROR | 500 | Server error |

---

## Pagination

All list endpoints support pagination with the following parameters:

- `page` - Page number (1-based, default: 1)
- `page_size` - Items per page (default: 20, max: 100)

### Pagination Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 156,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## Sorting

Use `sort_by` and `sort_order` parameters:

```
GET /admin/users?sort_by=last_login_at&sort_order=desc
```

**Common sort fields:**
- `created_at`
- `updated_at`
- `last_login_at`
- `email`
- `first_name`
- `last_name`

---

## Filtering

### Date Range
```
GET /admin/users?created_from=2024-01-01&created_to=2024-01-31
```

### Multiple Filters
```
GET /admin/users?role=User&is_email_verified=true&status=active
```

### Search
```
GET /admin/users?search=john
```
Searches across `first_name`, `last_name`, and `email` fields.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |

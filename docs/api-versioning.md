# API Versioning & Policy Documentation

## Versioning Strategy

### URL Path Versioning
The User Management Portal API uses URL path versioning:
```
https://api.usermgmt.example.com/v1/auth/login
https://api.usermgmt.example.com/v2/auth/login  (future)
```

### Version Format
Versions follow semantic versioning principles:
- **Major (v1, v2)**: Breaking changes, new authentication schemes
- **Minor**: New endpoints, additional fields (backward compatible)
- **Patch**: Bug fixes, performance improvements

### Current Version
- **Version**: 1.0.0
- **Release Date**: Q1 2024
- **Status**: Active
- **Sunset Date**: TBD (minimum 12 months notice)

---

## Rate Limiting Policy

### Overview
Rate limiting is implemented to ensure API stability, prevent abuse, and provide fair usage across all consumers.

### Implementation Details

#### Algorithm: Sliding Window
- Uses Redis for distributed rate limit tracking
- Window slides continuously rather than resetting at fixed intervals
- More accurate than fixed windows, prevents thundering herd

#### Rate Limit Tiers

| Tier | Requests/Min | Requests/Hour | Requests/Day | Access Level |
|------|--------------|---------------|--------------|--------------|
| Authentication | 5 | 30 | 100 | Public |
| Password Reset | - | 3 | 10 | Public |
| Standard User | 100 | 5,000 | 50,000 | Authenticated |
| Manager | 200 | 10,000 | 100,000 | Manager Role |
| Admin | 200 | 15,000 | 200,000 | Admin Role |
| File Upload | 10 | 100 | 1,000 | Authenticated |

### Rate Limit Headers
Every API response includes these headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
X-RateLimit-Policy: 100;w=60
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in window |
| `X-RateLimit-Remaining` | Remaining requests in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |
| `X-RateLimit-Policy` | Rate limit policy (requests;window_seconds) |

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705312800
Retry-After: 60
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "details": {
      "retry_after": 60,
      "limit": 100,
      "window": "1 minute"
    }
  }
}
```

### Exemptions
The following endpoints are exempt from rate limiting:
- `GET /health` - Health checks
- Internal service-to-service calls (using service tokens)

---

## Breaking Changes Policy

### What Constitutes a Breaking Change
1. **Removing** an endpoint
2. **Removing** or **renaming** a field from response
3. **Changing** field data type
4. **Changing** authentication requirements
5. **Changing** URL path structure
6. **Changing** default behavior
7. **Removing** enum values
8. **Adding** new required parameters

### Non-Breaking Changes
1. Adding new endpoints
2. Adding new optional parameters
3. Adding new fields to responses
4. Adding new enum values
5. Changing error messages (not codes)
6. Performance improvements

### Deprecation Process

#### Phase 1: Announcement (Day 0)
- Add deprecation notice to documentation
- Add `Deprecation` header to affected endpoints
- Send email notification to registered API consumers
- Update changelog

```http
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: </docs/migration-guide>; rel="migration"
```

#### Phase 2: Warning Period (Months 1-6)
- Continue serving deprecated endpoints
- Add warnings to API responses
- Provide migration guide
- Offer support for migration

#### Phase 3: Sunset Period (Months 7-12)
- Increase visibility of deprecation warnings
- Limit new features in deprecated endpoints
- Final migration reminders

#### Phase 4: Retirement (After 12 months)
- Return `410 Gone` status
- Provide error message with migration link
- Maintain documentation for reference

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "ENDPOINT_DEPRECATED",
    "message": "This endpoint has been retired. Please migrate to v2.",
    "documentation_url": "https://docs.usermgmt.example.com/migration/v1-to-v2"
  }
}
```

---

## API Changelog

### Version 1.0.0 (2024-01-15)
**Initial Release**

#### Features
- User registration with email verification
- JWT-based authentication (access + refresh tokens)
- User profile management
- Role-based access control (Admin, Manager, User)
- Admin user management dashboard
- Password reset via email
- Session management
- Audit logging
- Rate limiting

#### Endpoints
- 35+ RESTful endpoints
- OpenAPI 3.0 specification
- Comprehensive error handling

---

## Client Best Practices

### Handling Rate Limits
```python
import time
import requests

def api_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
            
        return response
    
    raise Exception("Max retries exceeded")
```

### Token Refresh Pattern
```python
class APIClient:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def request(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 401:
            # Token expired, refresh
            self.refresh_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.request(method, url, **kwargs)
        
        return response
    
    def refresh_access_token(self):
        response = requests.post('/auth/refresh', json={
            'refresh_token': self.refresh_token
        })
        data = response.json()
        self.access_token = data['data']['access_token']
```

### Exponential Backoff
```python
import random
import time

def exponential_backoff(attempt, base_delay=1, max_delay=60):
    """Calculate delay with exponential backoff and jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter

# Usage
for attempt in range(5):
    try:
        response = api_request()
        break
    except RateLimitError:
        delay = exponential_backoff(attempt)
        time.sleep(delay)
```

---

## Monitoring & Alerts

### Rate Limit Monitoring
- Track rate limit hits per endpoint
- Alert on unusual patterns
- Monitor burst traffic

### Key Metrics
| Metric | Threshold | Alert |
|--------|-----------|-------|
| Rate limit hits / min | > 100 | Warning |
| Rate limit hits / hour | > 1000 | Critical |
| Unique IPs rate limited | > 50 | Investigation |

### Dashboards
- Rate limit utilization by client
- Blocked requests over time
- Top rate-limited endpoints

---

## Support

For API versioning or rate limiting questions:
- Email: api-support@example.com
- Documentation: https://docs.usermgmt.example.com
- Status Page: https://status.usermgmt.example.com

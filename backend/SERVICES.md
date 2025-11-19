# Backend Services Documentation

This document describes the business logic services in the Peptimancer backend.

## Overview

Services contain reusable business logic separated from API routes. They handle:
- Data validation and transformation
- Database operations
- External API calls
- Business rule enforcement

---

## Service Modules

### 1. Authentication Service (`services/auth_service.py`)

**Purpose:** User authentication, OTP management, JWT token generation

**Key Functions:**

#### `generate_otp() -> str`
Generates a random 6-digit OTP code.

#### `create_magic_code(email: str) -> Dict`
Creates and stores a magic code (OTP) for email authentication.

**Returns:**
```python
{
    'code': '123456',  # Only in demo mode
    'expires_at': datetime
}
```

#### `verify_magic_code(email: str, code: str) -> Optional[Dict]`
Verifies a magic code and returns user data if valid.

**Returns:**
```python
{
    'id': 'user_xyz',
    'email': 'user@example.com',
    'role': 'researcher',
    'org_id': 'default'
}
```

#### `check_rate_limit(email: str) -> Dict`
Checks if user is rate-limited due to failed login attempts.

**Returns:**
```python
{
    'allowed': True/False,
    'retry_after': datetime  # If blocked
}
```

#### `create_jwt_token(user: Dict) -> str`
Creates a JWT token for the authenticated user.

**Configuration:**
- `OTP_LENGTH` - Length of OTP code (default: 6)
- `OTP_EXPIRES_MINUTES` - OTP expiry time (default: 10)
- `MAX_LOGIN_ATTEMPTS` - Max failed attempts (default: 5)
- `LOCKOUT_DURATION_MINUTES` - Lockout duration (default: 30)

---

### 2. Partner Share Service (`services/partner_share_service.py`)

**Purpose:** Secure share link management for partner portal

**Key Functions:**

#### `generate_share_token(share_id: str, file_id: str, expires_at: datetime) -> str`
Generates an HMAC-SHA256 signed share token.

**Format:** `share_id|file_id|expires_ts|signature`

#### `verify_share_token(token: str) -> Optional[Dict]`
Verifies a share token and extracts data.

**Returns:**
```python
{
    'share_id': 'uuid',
    'file_id': 'pack_123',
    'expires_at': datetime
}
```

#### `create_partner_share(reclaim_pack_id, recipient_org, recipient_email, created_by, policy) -> Dict`
Creates a new partner share with secure token.

**Returns:**
```python
{
    'share_id': 'uuid',
    'token': 'signed_token',
    'expires_at': datetime,
    'share_url': '/share/token'
}
```

#### `validate_share_access(share: Dict, client_ip: Optional[str]) -> Dict`
Validates if access to a share is allowed based on policies.

**Checks:**
- Share status (active/revoked/expired)
- Expiry date
- Download count limits
- IP whitelist

**Returns:**
```python
{
    'allowed': True/False,
    'reason': 'Error message if denied'
}
```

#### `revoke_share(share_id: str) -> bool`
Revokes a share link, making it inaccessible.

#### `cleanup_expired_shares() -> int`
Marks expired shares as expired. Returns count of shares updated.

**Configuration:**
- `PARTNER_SIGNING_SECRET` - HMAC signing key
- `PARTNER_SHARE_TTL_DAYS` - Default TTL (default: 14)
- `PARTNER_MAX_DOWNLOADS` - Default max downloads (default: 10)
- `WATERMARK_ENABLED` - Enable watermarking (default: true)

---

### 3. Chemistry Service (`services/chemistry_service.py`)

**Purpose:** Chemistry options and tier-based filtering

**Key Functions:**

#### `get_chemistry_options(tier: str = 'basic') -> Dict`
Gets chemistry modifications and exclusions filtered by user tier.

**Returns:**
```python
{
    'tier': 'basic',
    'mods': [
        {'key': 'acetylation', 'name': '...', 'tier': 'basic'}
    ],
    'exclusions': [
        {'key': 'no_cysteines', 'name': '...', 'tier': 'basic'}
    ]
}
```

#### `validate_modification_selection(modifications: List[str], user_tier: str) -> Dict`
Validates that selected modifications are allowed for user tier.

**Returns:**
```python
{
    'valid': True/False,
    'denied_mods': ['mod_id'],  # If invalid
    'message': 'Error message'
}
```

**Tier Hierarchy:**
- `basic` (0) - Base tier
- `pro` (1) - Premium tier
- `enterprise` (2) - Enterprise tier

**Access Rule:** User tier level must be >= required tier level

---

### 4. PatentPulse Service (`services/patentpulse_service.py`)

**Purpose:** Patent data queries and statistics

**Key Functions:**

#### `get_patent_items(status_filter, country, min_commercial_score, limit, skip) -> Dict`
Retrieves patent items with filters and pagination.

**Returns:**
```python
{
    'items': [...],
    'count': 10,
    'total': 1000,
    'skip': 0,
    'limit': 50
}
```

#### `get_patent_stats() -> Dict`
Calculates patent statistics and aggregations.

**Returns:**
```python
{
    'total': 1000,
    'by_status': {
        'Expired': 500,
        'Lapsed': 300
    },
    'top_assignees': [
        {'assignee': 'BigPharma', 'count': 100}
    ],
    'avg_commercial_score': 0.65,
    'avg_synthesis_score': 0.45,
    'avg_fto_risk': 0.25,
    'expiring_soon_24mo': 50
}
```

#### `get_top_opportunities(limit: int = 10) -> Dict`
Retrieves top patent opportunities ranked by viability score.

**Viability Score:**
```
viability = commercial_score * (1 - synthesis_score) * (1 - fto_risk)
```

**Returns:**
```python
{
    'opportunities': [
        {
            'patent_id': 'US1234567',
            'viability_score': 0.75,
            ...
        }
    ],
    'count': 10
}
```

#### `search_patents(query_text: str, limit: int) -> List[Dict]`
Full-text search on patent titles and abstracts.

---

### 5. Reclaim Service (`services/reclaim_service.py`)

**Purpose:** Reclaim pack export generation and management

**Key Functions:**

#### `generate_reclaim_pack(format, limit, country, status) -> Dict`
Generates a patent opportunity export (PDF or JSON).

**Returns:**
```python
{
    'file_id': 'uuid',
    'file_name': 'reclaim_pack_20250119.pdf',
    'format': 'pdf',
    'path': '/api/patentpulse/reclaim/uuid/download',
    'size_kb': 1024,
    'items': 10,
    'viability_avg': 0.75,
    'generated_at': 'ISO timestamp',
    'expires_at': 'ISO timestamp'
}
```

#### `list_exports(limit: int) -> Dict`
Lists recent exports sorted by generation date.

**Returns:**
```python
{
    'exports': [...],
    'count': 20
}
```

#### `get_export_metadata(file_id: str) -> Optional[Dict]`
Retrieves export metadata by file ID.

#### `validate_export_access(export: Dict) -> Dict`
Validates if an export can be accessed.

**Checks:**
- Expiry date
- File existence on disk

**Returns:**
```python
{
    'allowed': True/False,
    'reason': 'Error message if denied'
}
```

#### `delete_export(file_id: str) -> Dict`
Deletes an export (file and metadata).

**Returns:**
```python
{
    'success': True/False,
    'message': 'Result message'
}
```

---

## Service Design Patterns

### 1. Pure Functions
Services should be pure functions when possible:
```python
async def calculate_something(input: dict) -> dict:
    # No side effects
    # Same input = same output
    return result
```

### 2. Error Handling
Services return data or None, let routes handle HTTP errors:
```python
async def get_resource(id: str) -> Optional[dict]:
    resource = await db.collection.find_one({'id': id})
    return resource  # None if not found
```

### 3. Validation
Services validate business rules, not just types:
```python
async def create_share(data: dict) -> dict:
    # Validate business rules
    if data['max_downloads'] > 100:
        raise ValueError('Max downloads cannot exceed 100')
    
    # Create resource
    return result
```

### 4. Database Operations
Services handle database operations:
```python
async def save_resource(data: dict) -> dict:
    await db.collection.insert_one(data)
    return data
```

### 5. Configuration
Services read configuration from environment:
```python
import os

MAX_LIMIT = int(os.environ.get('MAX_LIMIT', '100'))
```

---

## Testing Services

### Unit Tests

Test services in isolation:
```python
import pytest
from services import auth_service

@pytest.mark.asyncio
async def test_generate_otp():
    code = auth_service.generate_otp()
    assert len(code) == 6
    assert code.isdigit()

@pytest.mark.asyncio
async def test_create_magic_code():
    result = await auth_service.create_magic_code('test@example.com')
    assert 'expires_at' in result
```

### Integration Tests

Test services with real database:
```python
@pytest.mark.asyncio
async def test_create_and_verify_code():
    email = 'test@example.com'
    
    # Create code
    result = await auth_service.create_magic_code(email)
    code = result['code']
    
    # Verify code
    user = await auth_service.verify_magic_code(email, code)
    assert user is not None
    assert user['email'] == email
```

---

## Adding a New Service

### 1. Create Service File

Create `services/my_service.py`:
```python
"""
My Service
Description of what this service does
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Configuration
CONFIG_VAR = os.environ.get('CONFIG_VAR', 'default')


async def do_something(param: str) -> Dict[str, Any]:
    """
    Description
    
    Args:
        param: Description
        
    Returns:
        Description
    """
    # Business logic
    result = {'data': param}
    return result
```

### 2. Add to Services Package

Update `services/__init__.py`:
```python
from . import my_service

__all__ = [
    'auth_service',
    'my_service',
    # ...
]
```

### 3. Use in Route

Use the service in your API route:
```python
from services import my_service

@router.post("/endpoint")
async def endpoint(body: Schema):
    result = await my_service.do_something(body.param)
    return result
```

### 4. Test

Create `tests/test_my_service.py`:
```python
import pytest
from services import my_service

@pytest.mark.asyncio
async def test_do_something():
    result = await my_service.do_something('test')
    assert result['data'] == 'test'
```

---

## Best Practices

### DO:
✅ Keep services focused on business logic  
✅ Make functions async when they do I/O  
✅ Return data dictionaries or domain objects  
✅ Log important operations  
✅ Validate inputs thoroughly  
✅ Use type hints  
✅ Write docstrings  

### DON'T:
❌ Handle HTTP requests directly  
❌ Return HTTP responses  
❌ Mix business logic with presentation logic  
❌ Use global state  
❌ Ignore errors  

---

## Related Documentation

- [Architecture Guide](../ARCHITECTURE.md)
- [API Reference](../API_REFERENCE.md)
- [Models Documentation](./models/README.md)
- [Schemas Documentation](./schemas/README.md)

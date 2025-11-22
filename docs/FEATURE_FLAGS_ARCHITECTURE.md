# Feature Flags Architecture

**Purpose:** Architectural framework for feature toggling and access control  
**Type:** UI scaffolding and placeholder system  
**Functionality:** None - purely structural

---

## Overview

This document describes the feature flags architecture implemented for Peptimancer. This system provides:
- Admin-controlled feature visibility toggles
- User-level access control (Levels 0-4)
- Placeholder UI components
- Mock API endpoints for UI scaffolding

**Important:** This system contains no biochemical, computational, or drug design functionality. It is purely an architectural framework for controlling UI visibility.

---

## Components

### Backend

#### 1. Schemas (`backend/schemas/feature_flags.py`)
Defines request/response models for feature flag operations:
- `FeatureFlagUpdate` - Update a feature flag
- `UserFeatureLevel` - Set user's access level
- `FeatureFlagResponse` - Feature flag state response

#### 2. Service (`backend/services/feature_flags_service.py`)
Handles feature flag business logic:
- `get_feature_flags()` - Retrieve all flags
- `update_feature_flag()` - Toggle a flag
- `get_user_feature_level()` - Get user's level
- `set_user_feature_level()` - Update user's level
- `log_feature_access()` - Audit logging

#### 3. Admin API (`backend/api/admin/feature_flags.py`)
Admin-only endpoints for managing flags:
- `GET /api/admin/features/flags` - List all flags
- `POST /api/admin/features/flags` - Update a flag
- `POST /api/admin/features/user-level` - Set user level
- `GET /api/admin/features/user-level/{user_id}` - Get user level
- `GET /api/admin/features/audit-log` - View audit log

#### 4. Placeholder API (`backend/api/placeholder.py`)
Mock endpoints returning dummy data:
- `GET /api/placeholder/advanced-preview` - Mock preview data
- `POST /api/placeholder/advanced-action` - Mock action response
- `GET /api/placeholder/feature-status` - User's feature status

### Frontend

#### 1. Admin Panel (`components/admin/FeatureFlagsPanel.js`)
UI for managing feature flags:
- Toggle global feature flags
- Set user feature levels
- View level descriptions

#### 2. Placeholder Panel (`components/PlaceholderPanel.js`)
Empty UI scaffolding that appears when features are "enabled":
- Shows placeholder data
- Demonstrates UI interaction
- No actual computation

---

## Feature Levels

### Level 0: Baseline
- Standard features only
- No advanced UI elements

### Level 1: Preview
- UI placeholders become visible
- Demonstrates level-gated UI

### Level 2: Extended
- Additional panels accessible
- More UI components shown

### Level 3: Advanced
- All UI components visible
- Full UI framework access

### Level 4: Maximum
- Complete architectural framework
- All placeholder elements enabled

**Note:** Levels only control UI visibility. No computational features exist at any level.

---

## Database Schema

### `feature_flags` Collection
```javascript
{
  _id: "global",
  flags: {
    advanced_mode_enabled: false,
    experimental_ui_enabled: false,
    preview_mode_enabled: false,
    extended_analytics_enabled: false
  },
  updated_at: "2025-01-19T12:00:00Z",
  updated_by: "admin@example.com"
}
```

### `users` Collection (Added Fields)
```javascript
{
  id: "user_xyz",
  // ... existing fields ...
  feature_level: 0,  // 0-4
  feature_level_updated_at: "2025-01-19T12:00:00Z",
  feature_level_updated_by: "admin@example.com"
}
```

### `feature_audit_log` Collection
```javascript
{
  user_id: "user_xyz",
  feature_key: "advanced_preview",
  level: 2,
  metadata: {},
  timestamp: "2025-01-19T12:00:00Z"
}
```

---

## API Endpoints

### Admin Endpoints (Require Admin Role)

**Get Feature Flags:**
```http
GET /api/admin/features/flags
Authorization: Cookie (JWT)

Response:
{
  "flags": {
    "advanced_mode_enabled": false,
    ...
  }
}
```

**Update Feature Flag:**
```http
POST /api/admin/features/flags
Content-Type: application/json

{
  "flag_key": "advanced_mode_enabled",
  "enabled": true,
  "config": null
}

Response:
{
  "flag_key": "advanced_mode_enabled",
  "enabled": true,
  "updated_at": "2025-01-19T12:00:00Z",
  "updated_by": "admin@example.com"
}
```

**Set User Feature Level:**
```http
POST /api/admin/features/user-level
Content-Type: application/json

{
  "user_id": "user_xyz",
  "feature_level": 2
}

Response:
{
  "user_id": "user_xyz",
  "feature_level": 2,
  "updated_at": "2025-01-19T12:00:00Z"
}
```

### Placeholder Endpoints (Require Authentication)

**Advanced Preview:**
```http
GET /api/placeholder/advanced-preview
Authorization: Cookie (JWT)

Response:
{
  "status": "preview_mode",
  "feature_level": 2,
  "available_features": ["feature_alpha", "feature_beta", null, null],
  "mock_data": {
    "example_field_1": "placeholder_value_1",
    ...
  },
  "message": "This is placeholder data only."
}
```

**Feature Status:**
```http
GET /api/placeholder/feature-status
Authorization: Cookie (JWT)

Response:
{
  "user_id": "user_xyz",
  "feature_level": 2,
  "global_flags": {...},
  "capabilities": {
    "level_0": "baseline",
    "level_1": "enabled",
    "level_2": "enabled",
    "level_3": "locked",
    "level_4": "locked"
  }
}
```

---

## Usage Example

### Admin: Enable a Feature Flag

```javascript
// Admin enables advanced mode
await fetch('/api/admin/features/flags', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    flag_key: 'advanced_mode_enabled',
    enabled: true
  }),
  credentials: 'include'
});
```

### Admin: Set User Level

```javascript
// Admin sets user to Level 2
await fetch('/api/admin/features/user-level', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    feature_level: 2
  }),
  credentials: 'include'
});
```

### User: Check Feature Status

```javascript
// User checks their feature status
const response = await fetch('/api/placeholder/feature-status', {
  credentials: 'include'
});
const data = await response.json();
console.log('My feature level:', data.feature_level);
```

### Frontend: Conditional Rendering

```javascript
// Show placeholder panel if level >= 1
function MyComponent() {
  const [featureLevel, setFeatureLevel] = useState(0);
  
  useEffect(() => {
    // Fetch user's feature level
    fetch('/api/placeholder/feature-status', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setFeatureLevel(data.feature_level));
  }, []);
  
  return (
    <div>
      {featureLevel >= 1 && <PlaceholderPanel featureLevel={featureLevel} />}
    </div>
  );
}
```

---

## Security

### Access Control
- All admin endpoints require `admin` role
- Placeholder endpoints require authentication
- Feature levels stored in database
- Audit log tracks all changes

### Authorization Flow
1. User authenticates (JWT in cookie)
2. Middleware extracts user role
3. Admin routes check for admin role
4. User routes check for valid session
5. Feature level retrieved from database
6. UI renders based on level

---

## Testing

### Test Feature Flags

```bash
# Get current flags (as admin)
curl -X GET http://localhost:8001/api/admin/features/flags \
  -H "Cookie: pmnc_jwt=YOUR_JWT"

# Toggle a flag
curl -X POST http://localhost:8001/api/admin/features/flags \
  -H "Content-Type: application/json" \
  -H "Cookie: pmnc_jwt=YOUR_JWT" \
  -d '{"flag_key": "advanced_mode_enabled", "enabled": true}'

# Set user level
curl -X POST http://localhost:8001/api/admin/features/user-level \
  -H "Content-Type: application/json" \
  -H "Cookie: pmnc_jwt=YOUR_JWT" \
  -d '{"user_id": "user_xyz", "feature_level": 2}'

# Get placeholder data (as user)
curl -X GET http://localhost:8001/api/placeholder/advanced-preview \
  -H "Cookie: pmnc_jwt=YOUR_JWT"
```

---

## Limitations

### What This System Does NOT Include:
- ❌ No biochemical computation
- ❌ No drug design functionality
- ❌ No affinity modeling
- ❌ No conjugate simulations
- ❌ No optimization algorithms
- ❌ No actionable chemistry

### What This System DOES Include:
- ✅ Feature visibility toggles
- ✅ User access level control
- ✅ Placeholder UI components
- ✅ Mock API responses
- ✅ Admin management panel
- ✅ Audit logging

---

## Future Considerations

This architectural framework can be extended for:
- Additional feature flags
- More granular permissions
- Feature rollout strategies
- A/B testing infrastructure
- Gradual feature enablement

However, any future extensions must remain within the bounds of UI/UX scaffolding and avoid implementing prohibited computational features.

---

## Maintenance

### Adding a New Flag

1. Add to DEFAULT_FLAGS in `services/feature_flags_service.py`
2. Document in this file
3. Update frontend components as needed

### Adding a New Level

1. Update level validation in service
2. Update UI descriptions
3. Update documentation

### Monitoring

Check audit logs regularly:
```javascript
// Get recent flag changes
await fetch('/api/admin/features/audit-log?limit=50');
```

---

## Related Documentation

- [Architecture Guide](../ARCHITECTURE.md)
- [Admin Documentation](./ADMIN_GUIDE.md)
- [API Reference](../API_REFERENCE.md)

# Authentication & Authorization Components

## Overview
This directory contains all authentication and role-based access control (RBAC) components for the application.

## Components

### Route Protection

#### `ProtectedRoute.js`
Wraps routes that require authentication (any logged-in user).
- Redirects to `/login` if not authenticated
- Stores `returnTo` parameter for post-login redirect
- Used for routes accessible to all authenticated users

**Usage:**
```jsx
<Route path="/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>} />
```

#### `AdminRoute.js`
Wraps routes that require admin role.
- Redirects to `/login` if not authenticated
- Shows "Access Denied" page if authenticated but not admin
- Used for admin-only features

**Usage:**
```jsx
<Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
```

#### **Future: `ResearcherRoute.js` (TODO)**
Will wrap routes accessible to researchers and admins.
- Similar to AdminRoute but checks for researcher OR admin role
- Use for intermediate-level features

#### **Future: `PartnerRoute.js` (TODO)**
Will wrap routes accessible to partners, researchers, and admins.
- Hierarchical access: partner < researcher < admin
- Use for partner collaboration features

---

### UI Components

#### `RoleBadge.js`
Displays current user's role as a badge in the navigation.
- Shows role icon and label
- Color-coded by role type
- Configurable size (sm, md, lg)

**Usage:**
```jsx
<RoleBadge user={user} size="sm" showIcon={true} />
```

#### `RoleGate.js`
Conditionally renders UI elements based on user role.
- Hide/show features without route changes
- Supports fallback content
- Future-proof for multiple role types

**Usage:**
```jsx
<RoleGate user={user} requireAdmin>
  <AdminOnlyPanel />
</RoleGate>

<RoleGate user={user} requireResearcher fallback={<LockedFeature />}>
  <ResearcherFeature />
</RoleGate>
```

---

## Utilities

### `/lib/roles.js`
Central role constants and utility functions.

**Constants:**
- `ROLES` - Role string constants
- `ROLE_LABELS` - Display names
- `ROLE_COLORS` - UI color schemes

**Helper Functions:**
- `hasRole(user, role)` - Check specific role
- `isAdmin(user)` - Check admin role
- `isResearcher(user)` - Check researcher role (future)
- `isPartner(user)` - Check partner role (future)
- `canAccessAdmin(user)` - Admin feature access
- `canAccessResearch(user)` - Research feature access (future)
- `canAccessPartner(user)` - Partner feature access (future)

---

## Current Role Hierarchy

```
admin (full access)
  └─> All admin features
  └─> All authenticated features

user (authenticated, limited access)
  └─> Standard features only
  └─> No admin access

anonymous (not logged in)
  └─> Public routes only
```

---

## Future Role Hierarchy (Planned)

```
admin (full access)
  └─> All features

researcher (intermediate access)
  └─> Research-level features
  └─> Standard features
  └─> Limited admin visibility

partner (basic elevated access)
  └─> Partner collaboration features
  └─> Standard features

user (authenticated)
  └─> Standard features only

anonymous
  └─> Public routes only
```

---

## Adding a New Role

When adding a new role (e.g., researcher):

1. **Add to constants** (`/lib/roles.js`):
   ```js
   ROLES.RESEARCHER = 'researcher';
   ROLE_LABELS[ROLES.RESEARCHER] = 'Researcher';
   ROLE_COLORS[ROLES.RESEARCHER] = '...';
   ```

2. **Update helper functions**:
   ```js
   export function isResearcher(user) {
     return user?.role === ROLES.RESEARCHER || user?.role === ROLES.ADMIN;
   }
   ```

3. **Create route component** (if needed):
   - Copy `AdminRoute.js` → `ResearcherRoute.js`
   - Update role check logic
   - Update error messages

4. **Update navigation** (`MainApp.js`):
   ```jsx
   {canAccessResearch(user) && (
     <Link to="/research">Research Dashboard</Link>
   )}
   ```

5. **Backend alignment**:
   - Ensure backend middleware has matching role
   - Update `require_role()` calls in FastAPI
   - Test authentication flow

---

## Testing RBAC

### Manual Testing
1. Create test users with different roles in MongoDB
2. Log in as each user type
3. Verify navigation visibility
4. Verify route access/denial
5. Check role badge display

### Automated Testing (TODO)
- Unit tests for role utility functions
- Integration tests for route protection
- E2E tests for role-based UI hiding

---

## Security Notes

⚠️ **Frontend RBAC is for UX only**
- All security enforcement happens on the backend
- Frontend role checks prevent confusing UX, not unauthorized access
- Never trust client-side role validation for security decisions

✅ **Backend Authorization**
- Every protected endpoint must check roles server-side
- Use `require_role()` middleware in FastAPI
- Log all admin actions for audit trail

---

## Future Enhancements (Documented, Not Implemented)

### Session Expiry Warning (TODO)
- Show toast notification 5 minutes before session expires
- Allow user to extend session
- Auto-logout on expiry

### Breadcrumbs (TODO)
- Show navigation path with role context
- Indicate protected areas
- Quick navigation

### Audit Logging (TODO)
- Log route access by role
- Track admin actions
- Export audit reports

---

## Questions?
See `/lib/roles.js` for role utility functions and constants.

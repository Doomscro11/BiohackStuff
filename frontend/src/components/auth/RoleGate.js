import React from 'react';
import { canAccessAdmin, canAccessResearch, canAccessPartner } from '@/lib/roles';

/**
 * RoleGate Component
 * Conditionally renders children based on user role
 * 
 * Usage:
 * <RoleGate user={user} requireAdmin>
 *   <AdminOnlyComponent />
 * </RoleGate>
 * 
 * Props:
 * - user: User object with role property
 * - requireAdmin: Boolean - requires admin role
 * - requireResearcher: Boolean - requires researcher role or higher (future)
 * - requirePartner: Boolean - requires partner role or higher (future)
 * - fallback: React element to show if access denied (optional)
 * - children: Content to render if access granted
 */
function RoleGate({ 
  user, 
  requireAdmin = false,
  requireResearcher = false,
  requirePartner = false,
  fallback = null,
  children 
}) {
  // Check access based on requirements
  let hasAccess = true;

  if (requireAdmin) {
    hasAccess = canAccessAdmin(user);
  } else if (requireResearcher) {
    // Future: Will check for researcher or admin role
    hasAccess = canAccessResearch(user);
  } else if (requirePartner) {
    // Future: Will check for partner, researcher, or admin role
    hasAccess = canAccessPartner(user);
  }

  // If no access, show fallback or nothing
  if (!hasAccess) {
    return fallback;
  }

  // Render children if access granted
  return <>{children}</>;
}

/**
 * Hook version for programmatic role checking
 * Returns boolean indicating if user has required access
 */
export function useRoleAccess(user, { admin = false, researcher = false, partner = false } = {}) {
  if (admin) return canAccessAdmin(user);
  if (researcher) return canAccessResearch(user);
  if (partner) return canAccessPartner(user);
  return true; // No specific role required
}

export default RoleGate;

/**
 * User Role Constants and Utilities
 * 
 * Central definition of user roles for RBAC system
 * Future-proofing: Ready for researcher and partner roles
 */

// Role constants
export const ROLES = {
  ADMIN: 'admin',
  RESEARCHER: 'researcher',  // Future: intermediate access level
  PARTNER: 'partner',        // Future: external partner access
  USER: 'user',              // Default authenticated user
  ANONYMOUS: 'anonymous'     // Not authenticated
};

// Role display names for UI
export const ROLE_LABELS = {
  [ROLES.ADMIN]: 'Admin',
  [ROLES.RESEARCHER]: 'Researcher',
  [ROLES.PARTNER]: 'Partner',
  [ROLES.USER]: 'User',
  [ROLES.ANONYMOUS]: 'Guest'
};

// Role badge colors for UI
export const ROLE_COLORS = {
  [ROLES.ADMIN]: 'bg-purple-100 text-purple-700 border-purple-200',
  [ROLES.RESEARCHER]: 'bg-blue-100 text-blue-700 border-blue-200',
  [ROLES.PARTNER]: 'bg-green-100 text-green-700 border-green-200',
  [ROLES.USER]: 'bg-gray-100 text-gray-700 border-gray-200',
  [ROLES.ANONYMOUS]: 'bg-gray-50 text-gray-500 border-gray-100'
};

/**
 * Check if user has a specific role
 * @param {Object} user - User object with role property
 * @param {string} requiredRole - Required role to check
 * @returns {boolean} True if user has the required role
 */
export function hasRole(user, requiredRole) {
  if (!user) return false;
  return user.role === requiredRole;
}

/**
 * Check if user has admin role
 * @param {Object} user - User object
 * @returns {boolean} True if user is admin
 */
export function isAdmin(user) {
  return hasRole(user, ROLES.ADMIN);
}

/**
 * Check if user has researcher role (or higher)
 * Future: Will include admin + researcher
 * @param {Object} user - User object
 * @returns {boolean} True if user is researcher or admin
 */
export function isResearcher(user) {
  if (!user) return false;
  // Future: return user.role === ROLES.RESEARCHER || user.role === ROLES.ADMIN;
  return user.role === ROLES.ADMIN; // For now, only admin has researcher-level access
}

/**
 * Check if user has partner role (or higher)
 * Future: Will include partner + researcher + admin
 * @param {Object} user - User object
 * @returns {boolean} True if user is partner, researcher, or admin
 */
export function isPartner(user) {
  if (!user) return false;
  // Future: return [ROLES.PARTNER, ROLES.RESEARCHER, ROLES.ADMIN].includes(user.role);
  return user.role === ROLES.ADMIN; // For now, only admin
}

/**
 * Get user role display name
 * @param {Object} user - User object
 * @returns {string} Display name for role
 */
export function getRoleLabel(user) {
  if (!user || !user.role) return ROLE_LABELS[ROLES.ANONYMOUS];
  return ROLE_LABELS[user.role] || ROLE_LABELS[ROLES.USER];
}

/**
 * Get role badge color classes
 * @param {Object} user - User object
 * @returns {string} CSS classes for role badge
 */
export function getRoleColor(user) {
  if (!user || !user.role) return ROLE_COLORS[ROLES.ANONYMOUS];
  return ROLE_COLORS[user.role] || ROLE_COLORS[ROLES.USER];
}

/**
 * Check if user can access admin features
 * @param {Object} user - User object
 * @returns {boolean} True if user can access admin features
 */
export function canAccessAdmin(user) {
  return isAdmin(user);
}

/**
 * Check if user can access researcher features
 * Future: Will be used for researcher-specific features
 * @param {Object} user - User object
 * @returns {boolean} True if user can access researcher features
 */
export function canAccessResearch(user) {
  return isResearcher(user);
}

/**
 * Check if user can access partner features
 * Future: Will be used for partner-specific features
 * @param {Object} user - User object
 * @returns {boolean} True if user can access partner features
 */
export function canAccessPartner(user) {
  return isPartner(user);
}

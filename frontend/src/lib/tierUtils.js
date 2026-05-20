/**
 * Tier Utilities
 * Handles tier-based feature access and rendering logic
 */

export const TIERS = {
  BASIC: 'basic',
  PRO: 'pro',
  ENTERPRISE: 'enterprise'
};

export const TIER_HIERARCHY = {
  basic: 0,
  pro: 1,
  enterprise: 2
};

/**
 * Check if user has access to a specific tier level
 * @param {string} userTier - User's current tier
 * @param {string} requiredTier - Required tier for feature
 * @returns {boolean} True if user has access
 */
export function hasAccessToTier(userTier, requiredTier) {
  const userLevel = TIER_HIERARCHY[userTier] || 0;
  const requiredLevel = TIER_HIERARCHY[requiredTier] || 0;
  return userLevel >= requiredLevel;
}

/**
 * Get tier display information
 * @param {string} tier - Tier name
 * @returns {Object} Display properties for tier
 */
export function getTierDisplay(tier) {
  const displays = {
    basic: {
      name: 'Basic',
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-100 dark:bg-gray-800',
      borderColor: 'border-gray-300 dark:border-gray-600',
      badge: 'bg-gray-100 text-gray-800 border-gray-300'
    },
    pro: {
      name: 'Pro',
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      borderColor: 'border-purple-300 dark:border-purple-600',
      badge: 'bg-purple-100 text-purple-800 border-purple-300'
    },
    enterprise: {
      name: 'Enterprise',
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      borderColor: 'border-blue-300 dark:border-blue-600',
      badge: 'bg-blue-100 text-blue-800 border-blue-300'
    }
  };

  return displays[tier] || displays.basic;
}

/**
 * Get upgrade message for locked feature
 * @param {string} featureName - Name of the locked feature
 * @param {string} requiredTier - Tier required to unlock
 * @returns {string} Upgrade message
 */
export function getUpgradeMessage(featureName, requiredTier = 'pro') {
  const tierDisplay = getTierDisplay(requiredTier);
  return `${featureName} is a ${tierDisplay.name} feature. Upgrade to access advanced modifications and analysis tools.`;
}

/**
 * Filter categories based on user tier
 * @param {Array} categories - All modification categories
 * @param {string} userTier - User's current tier
 * @param {boolean} isAdmin - Whether user is admin (admins see all)
 * @returns {Array} Filtered categories
 */
export function filterCategoriesByTier(categories, userTier, isAdmin = false) {
  if (isAdmin) {
    // Admins see everything
    return categories;
  }

  return categories.map(category => {
    const hasAccess = hasAccessToTier(userTier, category.proOnly ? 'pro' : 'basic');
    
    // Filter options within category based on tier
    const filteredOptions = category.options.filter(option => {
      return hasAccessToTier(userTier, option.tier || 'basic');
    });

    return {
      ...category,
      isLocked: !hasAccess,
      options: filteredOptions,
      lockedMessage: hasAccess ? null : getUpgradeMessage(category.title, 'pro')
    };
  });
}

/**
 * Get tier badge component props
 * @param {string} tier - Tier name
 * @returns {Object} Props for Badge component
 */
export function getTierBadgeProps(tier) {
  const display = getTierDisplay(tier);
  return {
    variant: 'outline',
    className: `text-xs ${display.badge}`
  };
}

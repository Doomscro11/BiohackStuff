import React from 'react';
import { Shield, Users, Briefcase, User } from 'lucide-react';
import { ROLES, getRoleLabel, getRoleColor } from '@/lib/roles';

/**
 * RoleBadge Component
 * Displays the current user's role as a badge in the navigation
 * 
 * Props:
 * - user: User object with role property
 * - showIcon: Boolean to show/hide role icon (default: true)
 * - size: 'sm' | 'md' | 'lg' (default: 'sm')
 */
function RoleBadge({ user, showIcon = true, size = 'sm' }) {
  if (!user || !user.role) return null;

  const roleLabel = getRoleLabel(user);
  const colorClasses = getRoleColor(user);
  
  // Icon mapping
  const roleIcons = {
    [ROLES.ADMIN]: Shield,
    [ROLES.RESEARCHER]: Users,
    [ROLES.PARTNER]: Briefcase,
    [ROLES.USER]: User
  };
  
  const Icon = roleIcons[user.role] || User;
  
  // Size variants
  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2'
  };
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  return (
    <div 
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${colorClasses} ${sizeClasses[size]}`}
      title={`Role: ${roleLabel}`}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      <span>{roleLabel}</span>
    </div>
  );
}

export default RoleBadge;

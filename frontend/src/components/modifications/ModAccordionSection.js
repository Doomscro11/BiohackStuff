/**
 * ModAccordionSection Component
 * Individual accordion section for modification categories
 * UI-only, no computational chemistry
 */

import React, { useState } from 'react';
import { ChevronDown, Lock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

function ModAccordionSection({
  id,
  title,
  options = [],
  selectedValues = [],
  onChange,
  isExpanded = false,
  onToggle,
  isLocked = false,
  lockedMessage = "Pro Feature — Upgrade to Access",
  hasWarning = false,
  warningMessage = "",
  proOnly = false
}) {
  const selectedCount = selectedValues.length;

  const handleCheckboxChange = (optionId) => {
    if (isLocked) return;
    
    if (selectedValues.includes(optionId)) {
      onChange(selectedValues.filter(v => v !== optionId));
    } else {
      onChange([...selectedValues, optionId]);
    }
  };

  return (
    <div className={`
      border rounded-lg overflow-hidden mb-3 transition-all duration-200
      ${hasWarning ? 'border-red-400 shadow-md' : 'border-gray-200 dark:border-gray-700'}
      ${isLocked ? 'opacity-60' : ''}
    `}>
      {/* Accordion Header */}
      <button
        type="button"
        onClick={onToggle}
        className={`
          w-full px-4 py-3 flex items-center justify-between
          bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750
          transition-colors duration-150
          ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <div className="flex items-center gap-3">
          {/* Chevron Icon */}
          <ChevronDown 
            className={`h-5 w-5 text-gray-500 transition-transform duration-200 ${
              isExpanded ? 'rotate-180' : ''
            }`}
          />
          
          {/* Title */}
          <span className="font-semibold text-gray-900 dark:text-white">
            {title}
          </span>
          
          {/* Pro Badge */}
          {proOnly && (
            <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-300">
              Pro
            </Badge>
          )}
          
          {/* Selected Count */}
          {selectedCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {selectedCount} selected
            </Badge>
          )}
          
          {/* Lock Icon */}
          {isLocked && (
            <Lock className="h-4 w-4 text-gray-400" />
          )}
        </div>

        {/* Warning Indicator */}
        {hasWarning && (
          <Badge variant="destructive" className="text-xs">
            ⚠ Conflict
          </Badge>
        )}
      </button>

      {/* Accordion Content */}
      {isExpanded && (
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          {/* Locked Message */}
          {isLocked && (
            <div className="mb-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
              <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
                <Lock className="h-4 w-4" />
                {lockedMessage}
              </p>
            </div>
          )}

          {/* Warning Message */}
          {hasWarning && (
            <div className="mb-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-sm text-red-800 dark:text-red-200">
                ⚠ {warningMessage}
              </p>
            </div>
          )}

          {/* Options List */}
          <div className="space-y-2">
            {options.map((option) => (
              <label
                key={option.id}
                className={`
                  flex items-start space-x-3 p-2 rounded-md
                  ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer hover:bg-white dark:hover:bg-gray-800'}
                  transition-colors duration-150
                `}
              >
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option.id)}
                  onChange={() => handleCheckboxChange(option.id)}
                  disabled={isLocked}
                  className="mt-1 h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {option.label}
                    </span>
                    {option.default && (
                      <Badge variant="outline" className="text-xs">
                        Default
                      </Badge>
                    )}
                  </div>
                  {option.notes && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {option.notes}
                    </p>
                  )}
                </div>
              </label>
            ))}
          </div>

          {/* Empty State */}
          {options.length === 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
              No options available
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default ModAccordionSection;

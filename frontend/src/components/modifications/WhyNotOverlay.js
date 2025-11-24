/**
 * WhyNotOverlay Component
 * Blocking overlay that appears when invalid modification combinations are selected
 * Provides explanation and quick fix options
 * 
 * IMPORTANT: All logic is mock/placeholder for UI demonstration only.
 */

import React from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

function WhyNotOverlay({ 
  isOpen, 
  onClose, 
  conflicts = [],
  onFixForMe,
  onContinueAnyway 
}) {
  if (!isOpen || conflicts.length === 0) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 z-50" />

      {/* Overlay */}
      <div className="fixed inset-x-4 top-1/2 -translate-y-1/2 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-xl bg-white dark:bg-gray-800 rounded-lg shadow-2xl z-50">
        {/* Header */}
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-6 py-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/40 rounded-full">
              <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-1">
                ❌ This Combination is Not Recommended
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300">
                The modifications you've selected have {conflicts.length} potential {conflicts.length === 1 ? 'conflict' : 'conflicts'}
              </p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="-mt-1 -mr-2"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
          {/* Conflicts List */}
          {conflicts.map((conflict, idx) => (
            <Alert key={idx} variant="destructive" className="border-red-300 dark:border-red-800">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <h4 className="font-semibold text-sm">
                    {conflict.title}
                  </h4>
                </div>
                <AlertDescription className="text-sm">
                  {conflict.description}
                </AlertDescription>
                <div className="flex flex-wrap gap-1 mt-2">
                  {conflict.matchedMods?.map((mod, modIdx) => (
                    <Badge key={modIdx} variant="outline" className="text-xs">
                      {mod}
                    </Badge>
                  ))}
                </div>
              </div>
            </Alert>
          ))}

          {/* Mock Suggestions */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
              Suggestions (Mock)
            </h4>
            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">1.</span>
                <span>Remove one of the conflicting modifications to resolve the issue</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">2.</span>
                <span>Consider alternative modification strategies that achieve similar goals</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">3.</span>
                <span>Use the "Fix This For Me" button to automatically resolve conflicts</span>
              </li>
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-3">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              <strong>Note:</strong> These warnings are based on mock rules for demonstration purposes. 
              This system does not perform real chemical analysis.
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex flex-col sm:flex-row gap-3">
            {onFixForMe && (
              <Button 
                onClick={onFixForMe}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                Fix This For Me (Auto-resolve)
              </Button>
            )}
            <Button 
              onClick={onClose}
              variant="outline"
              className="flex-1"
            >
              I'll Fix It Manually
            </Button>
            {onContinueAnyway && (
              <Button 
                onClick={onContinueAnyway}
                variant="ghost"
                className="text-xs text-gray-600 dark:text-gray-400"
              >
                Continue Anyway
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default WhyNotOverlay;

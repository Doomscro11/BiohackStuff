/**
 * RationalePopover Component
 * Displays detailed rationale for guardrail warnings
 * 
 * IMPORTANT: All content is mock/placeholder data for UI only.
 * No real chemical analysis is performed.
 */

import React from 'react';
import { X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getSeverityIcon } from '@/lib/guardrails';

function RationalePopover({ warning, onClose, isOpen }) {
  if (!isOpen || !warning) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Popover */}
      <div className="fixed inset-x-4 top-1/2 -translate-y-1/2 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-2xl z-50 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getSeverityIcon(warning.severity)}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {warning.title}
                </h3>
                <Badge 
                  variant="outline" 
                  className="mt-1"
                >
                  {warning.severity.toUpperCase()} Severity
                </Badge>
              </div>
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
        <div className="px-6 py-4 space-y-4">
          {/* Description */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Overview
            </h4>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {warning.description}
            </p>
          </div>

          {/* Affected Modifications */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Affected Modifications
            </h4>
            <div className="flex flex-wrap gap-2">
              {warning.matchedMods?.map((mod, idx) => (
                <Badge key={idx} variant="secondary" className="text-sm py-1">
                  {mod}
                </Badge>
              ))}
            </div>
          </div>

          {/* Detailed Rationale */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Detailed Rationale (Mock)
            </h4>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-4 border border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {warning.rationale}
              </p>
            </div>
          </div>

          {/* Mock Suggestions */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Suggestions (Mock)
            </h4>
            <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Consider removing one of the conflicting modifications</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Review alternative modification strategies that don't overlap</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Consult literature for similar peptide modification approaches (placeholder)</span>
              </li>
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-3">
            <div className="flex gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                  Important Notice
                </p>
                <p className="text-xs text-yellow-700 dark:text-yellow-300">
                  This rationale is based on mock rules for UI demonstration only. 
                  No real chemical modeling, structural analysis, or biochemical predictions are performed by this system.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <Button type="button" onClick={onClose} className="w-full">
            Close
          </Button>
        </div>
      </div>
    </>
  );
}

export default RationalePopover;

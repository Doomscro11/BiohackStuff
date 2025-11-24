/**
 * GuardrailEngine Component
 * Evaluates selected modifications against mock guardrail rules
 * 
 * CRITICAL: This performs NO real chemistry or molecular modeling.
 * All evaluations are based on mock rules for UI demonstration only.
 */

import React, { useMemo } from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getApplicableGuardrails, getSeverityColor, getSeverityIcon } from '@/lib/guardrails';

function GuardrailEngine({
  selectedModifications = [],
  onWarningClick,
  showDetails = true
}) {
  // Get applicable guardrails based on selected modifications
  const warnings = useMemo(() => {
    // Flatten all selected modifications from categories
    const allSelected = [];
    Object.keys(selectedModifications).forEach(category => {
      if (Array.isArray(selectedModifications[category])) {
        allSelected.push(...selectedModifications[category]);
      }
    });

    return getApplicableGuardrails(allSelected);
  }, [selectedModifications]);

  if (warnings.length === 0) {
    return showDetails ? (
      <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <div className="flex items-center gap-2">
          <Info className="h-5 w-5 text-green-600 dark:text-green-400" />
          <p className="text-sm text-green-800 dark:text-green-200">
            No conflicts detected. Your modification selections appear compatible. (Mock analysis only)
          </p>
        </div>
      </div>
    ) : null;
  }

  return (
    <div className="space-y-3">
      {/* Summary Badge */}
      {!showDetails && (
        <Badge variant="destructive" className="text-sm">
          {warnings.length} {warnings.length === 1 ? 'Warning' : 'Warnings'}
        </Badge>
      )}

      {/* Detailed Warnings */}
      {showDetails && (
        <>
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              Modification Compatibility Warnings (Mock)
            </h4>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              The following potential conflicts have been identified. These are mock warnings for UI demonstration only.
            </p>
          </div>

          {warnings.map((warning) => (
            <Alert
              key={warning.id}
              className={`${getSeverityColor(warning.severity)} border`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Warning Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{getSeverityIcon(warning.severity)}</span>
                    <h5 className="font-semibold text-sm">
                      {warning.title}
                    </h5>
                    <Badge 
                      variant="outline" 
                      className="text-xs"
                    >
                      {warning.severity.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Warning Description */}
                  <AlertDescription className="text-sm mb-2">
                    {warning.description}
                  </AlertDescription>

                  {/* Affected Modifications */}
                  <div className="mt-2">
                    <p className="text-xs font-medium mb-1">Affected modifications:</p>
                    <div className="flex flex-wrap gap-1">
                      {warning.matchedMods?.map((mod, idx) => (
                        <Badge 
                          key={idx} 
                          variant="secondary" 
                          className="text-xs"
                        >
                          {mod}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Why Button */}
                  {onWarningClick && (
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => onWarningClick(warning)}
                      className="p-0 h-auto mt-2 text-xs"
                    >
                      Why is this a problem? →
                    </Button>
                  )}
                </div>
              </div>
            </Alert>
          ))}

          {/* Disclaimer */}
          <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-md mt-4">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              <strong>Disclaimer:</strong> These warnings are based on mock rules for UI demonstration purposes only. 
              This system does not perform real chemistry analysis or molecular predictions.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

export default GuardrailEngine;

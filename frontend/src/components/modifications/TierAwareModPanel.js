/**
 * TierAwareModPanel Component
 * Wraps ModAccordionPanel with tier-based access control
 * Integrates with RBAC and feature flags
 */

import React, { useState, useEffect } from 'react';
import { Lock, Crown, Zap } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import ModAccordionPanel from './ModAccordionPanel';
import GuardrailEngine from './GuardrailEngine';
import RationalePopover from './RationalePopover';
import WhyNotOverlay from './WhyNotOverlay';
import { MODIFICATION_CATEGORIES } from '@/lib/modificationCategories';
import { getApplicableGuardrails } from '@/lib/guardrails';
import { filterCategoriesByTier, getTierDisplay, hasAccessToTier } from '@/lib/tierUtils';
import { canAccessAdmin } from '@/lib/roles';

function TierAwareModPanel({ 
  user, 
  selectedModifications,
  onChange,
  onGuardrailClick 
}) {
  const [selectedRationaleWarning, setSelectedRationaleWarning] = useState(null);
  const [showWhyNotOverlay, setShowWhyNotOverlay] = useState(false);
  const [highSeverityConflicts, setHighSeverityConflicts] = useState([]);

  // Get user tier and role
  const userTier = user?.tier || 'basic';
  const isAdmin = canAccessAdmin(user);
  const tierDisplay = getTierDisplay(userTier);

  // Filter categories based on tier
  const availableCategories = filterCategoriesByTier(
    MODIFICATION_CATEGORIES,
    userTier,
    isAdmin
  );

  // Get applicable guardrails
  const allSelectedMods = Object.values(selectedModifications || {}).flat();
  const warnings = getApplicableGuardrails(allSelectedMods);
  const highSeverityWarnings = warnings.filter(w => w.severity === 'high');

  // Auto-show overlay for high severity conflicts
  useEffect(() => {
    if (highSeverityWarnings.length > 0) {
      setHighSeverityConflicts(highSeverityWarnings);
      setShowWhyNotOverlay(true);
    } else {
      setHighSeverityConflicts([]);
      setShowWhyNotOverlay(false);
    }
  }, [highSeverityWarnings.length]);

  const handleWarningClick = (warning) => {
    setSelectedRationaleWarning(warning);
    if (onGuardrailClick) {
      onGuardrailClick(warning);
    }
  };

  const handleFixForMe = () => {
    // Auto-resolve conflicts by removing the last selected conflicting modification
    if (highSeverityConflicts.length > 0) {
      const conflict = highSeverityConflicts[0];
      const modToRemove = conflict.matchedMods[conflict.matchedMods.length - 1];
      
      // Find and remove the modification
      const updated = { ...selectedModifications };
      Object.keys(updated).forEach(categoryId => {
        updated[categoryId] = updated[categoryId].filter(mod => mod !== modToRemove);
      });
      
      onChange(updated);
      setShowWhyNotOverlay(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tier Status Banner */}
      <div className={`p-4 rounded-lg border ${tierDisplay.borderColor} ${tierDisplay.bgColor}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {userTier === 'enterprise' && <Crown className={`h-5 w-5 ${tierDisplay.color}`} />}
            {userTier === 'pro' && <Zap className={`h-5 w-5 ${tierDisplay.color}`} />}
            {userTier === 'basic' && <Lock className={`h-5 w-5 ${tierDisplay.color}`} />}
            <div>
              <h4 className={`text-sm font-semibold ${tierDisplay.color}`}>
                {tierDisplay.name} Tier Active
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {userTier === 'basic' && 'Access to basic modifications. Upgrade to Pro for advanced PK extensions.'}
                {userTier === 'pro' && 'Full access to advanced modifications and guardrail analysis.'}
                {userTier === 'enterprise' && 'Complete access to all modification tools and admin features.'}
              </p>
            </div>
          </div>
          {userTier === 'basic' && (
            <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
              Upgrade to Pro
            </Button>
          )}
        </div>
      </div>

      {/* Admin Override Notice */}
      {isAdmin && (
        <Alert className="bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700">
          <AlertDescription className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Admin Mode:</strong> You have access to all modification tiers and can override tier restrictions.
          </AlertDescription>
        </Alert>
      )}

      {/* Guardrail Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-3">
          <GuardrailEngine
            selectedModifications={selectedModifications}
            onWarningClick={handleWarningClick}
            showDetails={true}
          />
        </div>
      )}

      {/* Modification Accordion Panel */}
      <ModAccordionPanel
        categories={availableCategories}
        selectedModifications={selectedModifications}
        onChange={onChange}
        userTier={userTier}
        warnings={warnings.map(w => ({
          sectionId: w.category,
          message: w.title
        }))}
      />

      {/* Locked Features Summary */}
      {userTier === 'basic' && (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-start gap-3">
            <Lock className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div>
              <h5 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                Unlock Advanced Modifications
              </h5>
              <p className="text-xs text-yellow-700 dark:text-yellow-300 mb-2">
                Upgrade to Pro to access PK Extension, advanced protease resistance, and affinity tuning features.
              </p>
              <Button size="sm" variant="outline" className="text-xs">
                View Pro Features →
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Rationale Popover */}
      <RationalePopover
        warning={selectedRationaleWarning}
        isOpen={!!selectedRationaleWarning}
        onClose={() => setSelectedRationaleWarning(null)}
      />

      {/* Why Not Overlay */}
      <WhyNotOverlay
        isOpen={showWhyNotOverlay}
        onClose={() => setShowWhyNotOverlay(false)}
        conflicts={highSeverityConflicts}
        onFixForMe={handleFixForMe}
        onContinueAnyway={() => setShowWhyNotOverlay(false)}
      />
    </div>
  );
}

export default TierAwareModPanel;

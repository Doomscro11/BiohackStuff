/**
 * ModAccordionPanel Component
 * Main container for modification accordion system
 * Replaces cluttered modification checklists with organized accordion UI
 * UI-only, no computational chemistry
 */

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ModAccordionSection from './ModAccordionSection';

function ModAccordionPanel({
  categories = [],
  selectedModifications = {},
  onChange,
  userTier = 'basic',
  warnings = []
}) {
  const [expandedSections, setExpandedSections] = useState({});

  // Auto-expand sections with warnings
  useEffect(() => {
    const sectionsWithWarnings = warnings.map(w => w.sectionId).filter(Boolean);
    if (sectionsWithWarnings.length > 0) {
      setExpandedSections(prev => {
        const updated = { ...prev };
        sectionsWithWarnings.forEach(sectionId => {
          updated[sectionId] = true;
        });
        return updated;
      });
    }
  }, [warnings]);

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const expandAll = () => {
    const allExpanded = {};
    categories.forEach(cat => {
      allExpanded[cat.id] = true;
    });
    setExpandedSections(allExpanded);
  };

  const collapseAll = () => {
    setExpandedSections({});
  };

  const handleSectionChange = (sectionId, values) => {
    onChange({
      ...selectedModifications,
      [sectionId]: values
    });
  };

  const isAllExpanded = categories.every(cat => expandedSections[cat.id]);
  const isAllCollapsed = categories.every(cat => !expandedSections[cat.id]);

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Modification & Optimization
        </h3>
        <div className="flex gap-2">
          {!isAllExpanded && (
            <Button
              variant="outline"
              size="sm"
              onClick={expandAll}
              className="flex items-center gap-1"
            >
              <ChevronDown className="h-4 w-4" />
              Expand All
            </Button>
          )}
          {!isAllCollapsed && (
            <Button
              variant="outline"
              size="sm"
              onClick={collapseAll}
              className="flex items-center gap-1"
            >
              <ChevronUp className="h-4 w-4" />
              Collapse All
            </Button>
          )}
        </div>
      </div>

      {/* Accordion Sections */}
      <div className="space-y-3">
        {categories.map((category) => {
          const sectionWarnings = warnings.filter(w => w.sectionId === category.id);
          const hasWarning = sectionWarnings.length > 0;
          const warningMessage = sectionWarnings.map(w => w.message).join('; ');
          
          // Check if section is locked based on tier
          const isLocked = category.proOnly && userTier === 'basic';

          return (
            <ModAccordionSection
              key={category.id}
              id={category.id}
              title={category.title}
              options={category.options || []}
              selectedValues={selectedModifications[category.id] || []}
              onChange={(values) => handleSectionChange(category.id, values)}
              isExpanded={expandedSections[category.id] || false}
              onToggle={() => toggleSection(category.id)}
              isLocked={isLocked}
              lockedMessage={`${category.title} is a Pro feature. Upgrade to access advanced modifications.`}
              hasWarning={hasWarning}
              warningMessage={warningMessage}
              proOnly={category.proOnly}
            />
          );
        })}
      </div>

      {/* Empty State */}
      {categories.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <p>No modification categories available</p>
        </div>
      )}
    </div>
  );
}

export default ModAccordionPanel;

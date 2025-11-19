// Compact Analogue Generation Form with Accordion Layout
import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { Shield, Filter, Target, Beaker, Lock, AlertCircle } from 'lucide-react';

export default function AnalogueForm({
  formData,
  handleInputChange,
  chemOptions,
  conflictMsg,
  sequenceValidation,
  groupedMods
) {
  // Get user tier from window or default to basic
  const userTier = window.__USER_TIER__ || 'basic';
  
  const tierOrder = { basic: 0, pro: 1, enterprise: 2 };
  
  const canAccess = (requiredTier: string) => {
    return tierOrder[userTier as keyof typeof tierOrder] >= tierOrder[requiredTier as keyof typeof tierOrder];
  };
  
  const getTierBadge = (tier) => {
    if (tier === 'pro') return <Lock className="h-3 w-3 text-blue-600 inline ml-1" title="Pro tier required" />;
    if (tier === 'enterprise') return <Lock className="h-3 w-3 text-purple-600 inline ml-1" title="Enterprise tier required" />;
    return null;
  };
  
  const handleModToggle = (modKey: string) => {
    const current = formData.allowed_mods || [];
    if (current.includes(modKey)) {
      handleInputChange('allowed_mods', current.filter((k: string) => k !== modKey));
    } else {
      if (current.length < 3) {
        handleInputChange('allowed_mods', [...current, modKey]);
      }
    }
  };
  
  const handleExclusionToggle = (excKey: string) => {
    const current = formData.exclusions || [];
    if (current.includes(excKey)) {
      handleInputChange('exclusions', current.filter((k: string) => k !== excKey));
    } else {
      if (current.length < 6) {
        handleInputChange('exclusions', [...current, excKey]);
      }
    }
  };

  if (!chemOptions) {
    return (
      <div className="p-4 text-sm text-gray-500 text-center">
        Loading chemistry options...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Base Molecule */}
      <div className="space-y-2">
        <Label htmlFor="base_molecule" className="text-sm font-semibold">
          Base Molecule Sequence
        </Label>
        <Input
          id="base_molecule"
          value={formData.base_molecule}
          onChange={(e) => handleInputChange('base_molecule', e.target.value.toUpperCase())}
          placeholder="HAEGTFTSDVSSYLEG..."
          className="font-mono text-sm"
        />
        {sequenceValidation && (
          <div className="text-xs">
            {sequenceValidation.is_valid ? (
              <span className="text-green-600">✓ Valid sequence ({sequenceValidation.length} amino acids)</span>
            ) : (
              <span className="text-red-600">✗ {sequenceValidation.error || 'Invalid amino acid sequence'}</span>
            )}
          </div>
        )}
      </div>

      {/* Accordion Sections */}
      <Accordion type="multiple" defaultValue={['mods', 'target']} className="space-y-2">
        {/* Modification Strategy */}
        <AccordionItem value="mods" className="border rounded-lg bg-white">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-blue-600" />
              <span className="font-semibold">Modification Strategy</span>
              <Badge variant="secondary" className="text-xs">
                {formData.allowed_mods?.length || 0} / 3 selected
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs text-gray-500">
                Up to 3 modification classes · Tier: <b className="capitalize">{chemOptions.tier}</b>
              </div>
            </div>

            {conflictMsg && (
              <div className="mb-3 rounded bg-amber-50 border border-amber-200 text-amber-900 text-xs p-2 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{conflictMsg}</span>
              </div>
            )}

            <div className="space-y-3">
              {Object.entries(groupedMods).map(([group, items]: [string, any]) => (
                <div key={group} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs font-semibold text-gray-700 mb-2">{group}</div>
                  <div className="space-y-2">
                    {items.map((m) => {
                      const isLocked = !canAccess(m.tier);
                      const isSelected = formData.allowed_mods?.includes(m.key);
                      const isDisabled = isLocked || (!isSelected && (formData.allowed_mods?.length || 0) >= 3);
                      
                      return (
                        <label
                          key={m.key}
                          className={`flex items-start space-x-2 cursor-pointer p-2 rounded hover:bg-white transition-colors ${
                            isDisabled ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                          onClick={() => {
                            if (isLocked) {
                              window.location.href = '/billing';
                            } else if (!isDisabled) {
                              handleModToggle(m.key);
                            }
                          }}
                        >
                          <Checkbox
                            checked={isSelected}
                            disabled={isDisabled}
                            className="mt-0.5"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm flex items-center gap-1">
                              {m.label}
                              {getTierBadge(m.tier)}
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                              {m.notes}
                              {m.typical_targets?.length > 0 && (
                                <span className="ml-1">
                                  (targets: {m.typical_targets.join(', ')})
                                </span>
                              )}
                            </div>
                            {m.pk_intent?.length > 0 && (
                              <div className="text-xs text-blue-600 mt-0.5">
                                {m.pk_intent.join(' • ')}
                              </div>
                            )}
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Exclusion Clauses */}
        <AccordionItem value="exclusions" className="border rounded-lg bg-white">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-orange-600" />
              <span className="font-semibold">Exclusion Clauses</span>
              <Badge variant="secondary" className="text-xs">
                {formData.exclusions?.length || 0} / 6 selected
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4">
            <div className="text-xs text-gray-500 mb-3">
              Up to 6 exclusions · Specify constraints for the design
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {chemOptions.exclusions.map((e: any) => {
                const isLocked = !canAccess(e.tier);
                const isSelected = formData.exclusions?.includes(e.key);
                const isDisabled = isLocked || (!isSelected && (formData.exclusions?.length || 0) >= 6);
                
                return (
                  <label
                    key={e.key}
                    className={`flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-gray-50 transition-colors ${
                      isDisabled ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    onClick={() => {
                      if (isLocked) {
                        window.location.href = '/billing';
                      } else if (!isDisabled) {
                        handleExclusionToggle(e.key);
                      }
                    }}
                  >
                    <Checkbox
                      checked={isSelected}
                      disabled={isDisabled}
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm">
                        {e.label}
                        {getTierBadge(e.tier)}
                      </span>
                    </div>
                  </label>
                );
              })}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Target & Generation */}
        <AccordionItem value="target" className="border rounded-lg bg-white">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-green-600" />
              <span className="font-semibold">Target & Generation</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4">
            <div className="space-y-4">
              {/* Target Use */}
              <div className="space-y-2">
                <Label htmlFor="target_use" className="text-sm">Target Therapeutic Use</Label>
                <Textarea
                  id="target_use"
                  value={formData.target_use}
                  onChange={(e) => handleInputChange('target_use', e.target.value)}
                  placeholder="GLP-1 receptor agonist for diabetes treatment"
                  rows={2}
                  className="text-sm"
                />
              </div>

              {/* Generation Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="num_analogues" className="text-sm">Number of Analogues</Label>
                  <Select
                    value={formData.num_analogues.toString()}
                    onValueChange={(value) => handleInputChange('num_analogues', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select number" />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                        <SelectItem key={num} value={num.toString()}>{num}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="include_cost"
                      checked={formData.include_cost}
                      onCheckedChange={(checked) => handleInputChange('include_cost', checked)}
                    />
                    <Label htmlFor="include_cost" className="text-sm cursor-pointer">
                      Include synthesis cost estimates
                    </Label>
                  </div>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Summary Preview */}
      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-sm">
          <Beaker className="h-4 w-4 text-gray-500" />
          <span className="font-medium text-gray-700">Design Summary:</span>
          <span className="text-gray-600">
            {formData.allowed_mods?.length || 0} modifications •{' '}
            {formData.exclusions?.length || 0} exclusions •{' '}
            {formData.num_analogues} analogue{formData.num_analogues !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
    </div>
  );
}

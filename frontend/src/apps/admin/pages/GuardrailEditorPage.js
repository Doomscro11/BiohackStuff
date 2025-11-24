/**
 * Guardrail Editor Page
 * Admin-only page for managing mock guardrail rules
 * 
 * IMPORTANT: This edits mock rules only, no real chemistry
 */

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, Save, X, Download, Upload, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { GUARDRAILS } from '@/lib/guardrails';
import { getSeverityColor, getSeverityIcon } from '@/lib/guardrails';

function GuardrailEditorPage() {
  const [rules, setRules] = useState([...GUARDRAILS]);
  const [editingRule, setEditingRule] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  const handleToggleRule = (ruleId) => {
    setRules(rules.map(rule => 
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    ));
    setHasChanges(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule({ ...rule });
  };

  const handleSaveEdit = () => {
    if (editingRule) {
      setRules(rules.map(rule => 
        rule.id === editingRule.id ? editingRule : rule
      ));
      setEditingRule(null);
      setHasChanges(true);
    }
  };

  const handleDeleteRule = (ruleId) => {
    if (window.confirm('Are you sure you want to delete this rule?')) {
      setRules(rules.filter(rule => rule.id !== ruleId));
      setHasChanges(true);
    }
  };

  const handleAddRule = () => {
    const newRule = {
      id: `custom_rule_${Date.now()}`,
      title: 'New Custom Rule',
      description: 'Enter description here',
      applicableWhen: [],
      severity: 'low',
      rationale: 'Enter rationale here',
      category: 'general',
      enabled: true
    };
    setRules([...rules, newRule]);
    setEditingRule(newRule);
    setHasChanges(true);
  };

  const handleResetToDefaults = () => {
    if (window.confirm('Reset all rules to defaults? This will discard all custom rules.')) {
      setRules([...GUARDRAILS]);
      setHasChanges(false);
    }
  };

  const handleExportRules = () => {
    const dataStr = JSON.stringify(rules, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `guardrail_rules_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImportRules = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setRules(imported);
          setHasChanges(true);
          alert('Rules imported successfully');
        } catch (err) {
          alert('Error importing rules: Invalid JSON format');
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Guardrail Rule Editor
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage mock guardrail rules for modification compatibility warnings (UI demonstration only)
          </p>
        </div>

        {/* Actions Bar */}
        <div className="flex flex-wrap gap-3 mb-6">
          <Button onClick={handleAddRule} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add New Rule
          </Button>
          <Button onClick={handleResetToDefaults} variant="outline" className="flex items-center gap-2">
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </Button>
          <Button onClick={handleExportRules} variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Rules
          </Button>
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".json"
              onChange={handleImportRules}
              className="hidden"
            />
            <Button variant="outline" className="flex items-center gap-2" asChild>
              <span>
                <Upload className="h-4 w-4" />
                Import Rules
              </span>
            </Button>
          </label>
        </div>

        {/* Unsaved Changes Warning */}
        {hasChanges && (
          <Alert className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700">
            <AlertDescription className="text-yellow-800 dark:text-yellow-200">
              You have unsaved changes. Changes are stored in browser state only (mock data).
            </AlertDescription>
          </Alert>
        )}

        {/* Rules List */}
        <div className="space-y-4">
          {rules.map((rule) => (
            <Card key={rule.id} className="overflow-hidden">
              <CardHeader className="bg-white dark:bg-gray-800">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{getSeverityIcon(rule.severity)}</span>
                      <CardTitle className="text-lg">
                        {editingRule?.id === rule.id ? (
                          <input
                            type="text"
                            value={editingRule.title}
                            onChange={(e) => setEditingRule({ ...editingRule, title: e.target.value })}
                            className="px-2 py-1 border rounded w-full"
                          />
                        ) : (
                          rule.title
                        )}
                      </CardTitle>
                      <Badge 
                        variant="outline"
                        className={getSeverityColor(rule.severity).replace('bg-', 'border-')}
                      >
                        {rule.severity.toUpperCase()}
                      </Badge>
                      {rule.enabled === false && (
                        <Badge variant="secondary">Disabled</Badge>
                      )}
                    </div>
                    <CardDescription>
                      {editingRule?.id === rule.id ? (
                        <textarea
                          value={editingRule.description}
                          onChange={(e) => setEditingRule({ ...editingRule, description: e.target.value })}
                          className="px-2 py-1 border rounded w-full text-sm"
                          rows="2"
                        />
                      ) : (
                        rule.description
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {editingRule?.id === rule.id ? (
                      <>
                        <Button size="sm" onClick={handleSaveEdit}>
                          <Save className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditingRule(null)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button size="sm" variant="outline" onClick={() => handleEditRule(rule)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleToggleRule(rule.id)}
                        >
                          {rule.enabled === false ? 'Enable' : 'Disable'}
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleDeleteRule(rule.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              
              {editingRule?.id === rule.id && (
                <CardContent className="bg-gray-50 dark:bg-gray-900 pt-4">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Category</label>
                      <input
                        type="text"
                        value={editingRule.category}
                        onChange={(e) => setEditingRule({ ...editingRule, category: e.target.value })}
                        className="px-2 py-1 border rounded w-full text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Severity</label>
                      <select
                        value={editingRule.severity}
                        onChange={(e) => setEditingRule({ ...editingRule, severity: e.target.value })}
                        className="px-2 py-1 border rounded w-full text-sm"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Rationale (Mock)</label>
                      <textarea
                        value={editingRule.rationale}
                        onChange={(e) => setEditingRule({ ...editingRule, rationale: e.target.value })}
                        className="px-2 py-1 border rounded w-full text-sm"
                        rows="3"
                      />
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {rules.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                No guardrail rules defined
              </p>
              <Button onClick={handleAddRule}>
                Add First Rule
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Disclaimer */}
        <Alert className="mt-6 bg-gray-100 dark:bg-gray-800">
          <AlertDescription className="text-xs text-gray-600 dark:text-gray-400">
            <strong>Note:</strong> This rule editor modifies mock rules for UI demonstration only. 
            Changes are stored in browser state and do not affect any real chemical analysis systems.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}

export default GuardrailEditorPage;

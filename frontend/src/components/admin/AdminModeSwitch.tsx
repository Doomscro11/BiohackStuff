// Admin Mode Switch Component for Peptimancer Enterprise
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Settings, Shield, Clock, TrendingUp } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

interface Settings {
  integrationsMode: string;
  demoMode: boolean;
  watermarkExports: boolean;
  croEnabled: boolean;
  billingEnabled: boolean;
  rateLimitDemo: number;
  rateLimitLive: number;
  maxAnalogues: number;
  enterpriseFeatures: boolean;
  auditLogging: boolean;
}

interface SettingsInfo {
  settings: Settings;
  mode_info: {
    name: string;
    description: string;
    color: string;
    features: string[];
  };
  last_updated: string | null;
  last_updated_by: string | null;
  cache_ttl_seconds: number;
}

interface AuditRecord {
  _id: string;
  timestamp: string;
  actor: string;
  action: string;
  before: Settings;
  after: Settings;
  changes: Partial<Settings>;
}

export default function AdminModeSwitch() {
  const [settingsInfo, setSettingsInfo] = useState<SettingsInfo | null>(null);
  const [history, setHistory] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Load initial data
  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [settingsResponse, historyResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/settings`),
        fetch(`${BACKEND_URL}/api/admin/settings/history`)
      ]);

      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json();
        setSettingsInfo(settingsData);
      } else {
        throw new Error('Failed to load settings');
      }

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setHistory(historyData.history || []);
      } else {
        console.warn('Failed to load history');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (key: keyof Settings, value: any) => {
    if (!settingsInfo) return;
    
    setSettingsInfo({
      ...settingsInfo,
      settings: {
        ...settingsInfo.settings,
        [key]: value
      }
    });
  };

  const saveSettings = async () => {
    if (!settingsInfo || confirm !== 'SWITCH') return;

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...settingsInfo.settings,
          confirm
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(`Settings updated successfully. Changed: ${result.updated_fields.join(', ')}`);
        setConfirm('');
        await loadAdminData(); // Reload to get fresh data
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update settings');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const resetSettings = async () => {
    if (confirm !== 'SWITCH') return;

    setSaving(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/settings/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        setSuccess('Settings reset to defaults');
        setConfirm('');
        await loadAdminData();
      } else {
        throw new Error('Failed to reset settings');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to reset settings');
    } finally {
      setSaving(false);
    }
  };

  const getModeColor = (color: string) => {
    switch (color) {
      case 'green': return 'bg-green-100 border-green-300 text-green-800';
      case 'yellow': return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'red': return 'bg-red-100 border-red-300 text-red-800';
      default: return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <span className="ml-2">Loading admin panel...</span>
      </div>
    );
  }

  if (!settingsInfo) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load admin settings. Check your permissions and try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Shield className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Admin Control Panel</h1>
        </div>
        <p className="text-gray-600">Runtime configuration and mode switching for Peptimancer Enterprise</p>
      </div>

      {/* Current Mode Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Current System Mode
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`p-4 rounded-lg border-2 ${getModeColor(settingsInfo.mode_info.color)}`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg">{settingsInfo.mode_info.name}</h3>
              <Badge variant="outline">{settingsInfo.settings.integrationsMode.toUpperCase()}</Badge>
            </div>
            <p className="mb-3">{settingsInfo.mode_info.description}</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
              {settingsInfo.mode_info.features.map((feature, idx) => (
                <div key={idx} className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-current rounded-full" />
                  {feature}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Settings Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Runtime Settings</CardTitle>
          <CardDescription>
            Modify system behavior without redeployment. Changes take effect immediately.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Integration Mode */}
          <div className="space-y-2">
            <Label htmlFor="integrations-mode">Integration Mode</Label>
            <Select
              value={settingsInfo.settings.integrationsMode}
              onValueChange={(value) => updateSetting('integrationsMode', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="mock">Mock - Safe Development</SelectItem>
                <SelectItem value="sandbox">Sandbox - Test Environment</SelectItem>
                <SelectItem value="live">Live - Production</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Feature Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="demo-mode"
                checked={settingsInfo.settings.demoMode}
                onCheckedChange={(checked) => updateSetting('demoMode', checked)}
              />
              <Label htmlFor="demo-mode">Demo Mode</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="watermark-exports"
                checked={settingsInfo.settings.watermarkExports}
                onCheckedChange={(checked) => updateSetting('watermarkExports', checked)}
              />
              <Label htmlFor="watermark-exports">Watermark Exports</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="cro-enabled"
                checked={settingsInfo.settings.croEnabled}
                onCheckedChange={(checked) => updateSetting('croEnabled', checked)}
              />
              <Label htmlFor="cro-enabled">CRO Integration</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="billing-enabled"
                checked={settingsInfo.settings.billingEnabled}
                onCheckedChange={(checked) => updateSetting('billingEnabled', checked)}
              />
              <Label htmlFor="billing-enabled">Billing System</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="enterprise-features"
                checked={settingsInfo.settings.enterpriseFeatures}
                onCheckedChange={(checked) => updateSetting('enterpriseFeatures', checked)}
              />
              <Label htmlFor="enterprise-features">Enterprise Features</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="audit-logging"
                checked={settingsInfo.settings.auditLogging}
                onCheckedChange={(checked) => updateSetting('auditLogging', checked)}
              />
              <Label htmlFor="audit-logging">Audit Logging</Label>
            </div>
          </div>

          {/* Numeric Settings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="rate-limit-demo">Demo Rate Limit</Label>
              <Input
                id="rate-limit-demo"
                type="number"
                min="1"
                max="1000"
                value={settingsInfo.settings.rateLimitDemo}
                onChange={(e) => updateSetting('rateLimitDemo', parseInt(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="rate-limit-live">Live Rate Limit</Label>
              <Input
                id="rate-limit-live"
                type="number"
                min="1"
                max="10000"
                value={settingsInfo.settings.rateLimitLive}
                onChange={(e) => updateSetting('rateLimitLive', parseInt(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-analogues">Max Analogues</Label>
              <Input
                id="max-analogues"
                type="number"
                min="1"
                max="20"
                value={settingsInfo.settings.maxAnalogues}
                onChange={(e) => updateSetting('maxAnalogues', parseInt(e.target.value))}
              />
            </div>
          </div>

          {/* Confirmation and Actions */}
          <div className="border-t pt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="confirm">Type "SWITCH" to confirm changes</Label>
              <Input
                id="confirm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="SWITCH"
                className="max-w-xs"
              />
            </div>

            <div className="flex gap-3">
              <Button
                onClick={saveSettings}
                disabled={saving || confirm !== 'SWITCH'}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {saving ? 'Applying...' : 'Apply Changes'}
              </Button>

              <Button
                onClick={resetSettings}
                disabled={saving || confirm !== 'SWITCH'}
                variant="outline"
                className="text-orange-600 border-orange-300 hover:bg-orange-50"
              >
                Reset to Defaults
              </Button>
            </div>

            {success && (
              <Alert className="border-green-200 bg-green-50">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Audit History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Change History
          </CardTitle>
          <CardDescription>
            Recent configuration changes with audit trail
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-auto space-y-2">
            {history.length === 0 ? (
              <p className="text-gray-500 text-sm">No configuration changes recorded</p>
            ) : (
              history.map((record) => (
                <div key={record._id} className="border-l-4 border-blue-200 pl-4 py-2 text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{record.actor}</span>
                    <span className="text-gray-500">
                      {new Date(record.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-gray-700">
                    {record.action === 'settings_update' && (
                      <>Updated: {Object.keys(record.changes).join(', ')}</>
                    )}
                    {record.action === 'settings_initialized' && <>System initialized</>}
                    {record.action === 'settings_reset' && <>Settings reset to defaults</>}
                  </div>
                  {record.action === 'settings_update' && (
                    <div className="text-xs text-gray-500 mt-1">
                      Mode: {record.before.integrationsMode} → {record.after.integrationsMode}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
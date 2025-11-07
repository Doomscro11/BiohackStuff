// System Health Card Component
import React, { useEffect, useState } from 'react';
import { getHealth } from '../../lib/admin.ts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Database, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface HealthData {
  mode: string;
  demo: boolean;
  db: {
    latencyMs: number;
    ok: boolean;
  };
  services: {
    generateApi: boolean;
    exportApi: boolean;
    croWebhook: boolean;
    billing: boolean;
  };
  metrics: {
    runs: number;
    quotesBacklog: number;
    errors24h: number;
  };
  uptime: string;
}

export default function AdminHealthCard() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadHealth();
    // Refresh every 30 seconds
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    try {
      const data = await getHealth();
      // Ensure required fields exist
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid health data received');
      }
      setHealth(data);
      setError('');
    } catch (err: any) {
      console.error('Health check failed:', err);
      setError(err.message || 'Failed to load health metrics');
    } finally {
      setLoading(false);
    }
  };

  const StatusBadge = ({ ok }: { ok: boolean }) => (
    <Badge className={`${ok ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'} text-xs`}>
      {ok ? (
        <>
          <CheckCircle className="h-3 w-3 mr-1" />
          OK
        </>
      ) : (
        <>
          <AlertCircle className="h-3 w-3 mr-1" />
          Check
        </>
      )}
    </Badge>
  );

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="ml-2">Loading system health...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!health) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-600" />
          System Health
        </CardTitle>
        <CardDescription>
          Real-time monitoring of system status and metrics
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Mode Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-xs text-gray-500 mb-1">Mode</div>
            <div className="font-semibold text-sm">{health.mode ? health.mode.toUpperCase() : 'UNKNOWN'}</div>
            {health.demo && (
              <Badge className="mt-1 bg-yellow-100 text-yellow-700 text-xs">DEMO</Badge>
            )}
          </div>
          
          <div>
            <div className="text-xs text-gray-500 mb-1">DB Latency</div>
            <div className="font-semibold text-sm flex items-center gap-2">
              <Database className="h-4 w-4" />
              {health.db?.latencyMs || 'N/A'} ms
            </div>
            <StatusBadge ok={health.db?.ok || false} />
          </div>
          
          <div>
            <div className="text-xs text-gray-500 mb-1">System Uptime</div>
            <div className="font-semibold text-sm">{health.uptime || 'N/A'}</div>
          </div>
          
          <div>
            <div className="text-xs text-gray-500 mb-1">Status</div>
            <StatusBadge ok={health.db?.ok || false} />
          </div>
        </div>

        {/* Services Status */}
        <div>
          <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Services
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="flex items-center justify-between p-2 border rounded">
              <span className="text-xs">Generate API</span>
              <StatusBadge ok={health.services.generateApi} />
            </div>
            <div className="flex items-center justify-between p-2 border rounded">
              <span className="text-xs">Export API</span>
              <StatusBadge ok={health.services.exportApi} />
            </div>
            <div className="flex items-center justify-between p-2 border rounded">
              <span className="text-xs">CRO Webhook</span>
              <StatusBadge ok={health.services.croWebhook} />
            </div>
            <div className="flex items-center justify-between p-2 border rounded">
              <span className="text-xs">Billing</span>
              <StatusBadge ok={health.services.billing} />
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div>
          <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Metrics
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 border rounded">
              <div className="text-2xl font-bold text-blue-600">{health.metrics.runs}</div>
              <div className="text-xs text-gray-500 mt-1">Total Runs</div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-2xl font-bold text-amber-600">{health.metrics.quotesBacklog}</div>
              <div className="text-xs text-gray-500 mt-1">Quotes Backlog</div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-2xl font-bold text-red-600">{health.metrics.errors24h}</div>
              <div className="text-xs text-gray-500 mt-1">Errors (24h)</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

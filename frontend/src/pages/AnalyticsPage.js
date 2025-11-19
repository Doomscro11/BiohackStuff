// Admin Analytics Dashboard
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, TrendingUp, DollarSign, AlertCircle, Activity, BarChart3 } from 'lucide-react';
import { getLiveAnalytics, getSnapshots } from '../lib/analytics';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function AnalyticsPage() {
  const [live, setLive] = useState<LiveAnalytics | null>(null);
  const [snapshots, setSnapshots] = useState<AnalyticsSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load live and historical data
      const [liveResult, snapshotsResult] = await Promise.all([
        getLiveAnalytics(),
        getSnapshots(30)
      ]);

      if (!liveResult.ok) {
        throw new Error(`Failed to load live analytics: ${liveResult.text || 'Unknown error'}`);
      }

      if (!snapshotsResult.ok) {
        throw new Error(`Failed to load snapshots: ${snapshotsResult.text || 'Unknown error'}`);
      }

      setLive(liveResult.data);
      setSnapshots(snapshotsResult.data.snapshots);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Analytics Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map(i => (
              <Card key={i} className="animate-pulse">
                <CardContent className="pt-6">
                  <div className="h-16 bg-gray-200 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-900">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!live) {
    return null;
  }

  // Prepare chart data
  const analoguesTrendData = snapshots
    .slice()
    .reverse()
    .map(s => ({
      date: new Date(s.snapshot_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      analogues: s.analogues_24h
    }));

  const creditsTrendData = snapshots
    .slice()
    .reverse()
    .map(s => ({
      date: new Date(s.snapshot_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      purchased: s.credits_purchased_24h,
      consumed: s.credits_consumed_24h
    }));

  const modMixData = Object.entries(live.mod_group_mix_24h).map(([key, value]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    count: value
  }));

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600">Last 24 hours and 30-day trends</p>
        </div>

        {/* Metric Tiles */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Active Users */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <Users className="h-4 w-4 text-blue-600" />
                Active Users (24h)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{live.users_active_24h}</div>
            </CardContent>
          </Card>

          {/* Analogues */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                Analogues Generated (24h)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{live.analogues_24h}</div>
            </CardContent>
          </Card>

          {/* Net Credits Flow */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-purple-600" />
                Net Credits Flow (24h)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-bold ${live.net_flow_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {live.net_flow_24h > 0 ? '+' : ''}{live.net_flow_24h}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                ↑ {live.credits_purchased_24h} purchased · ↓ {live.credits_consumed_24h} consumed
              </div>
            </CardContent>
          </Card>

          {/* Error Rate */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                Errors (24h)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">{live.errors_24h}</div>
              {live.latency_p95_ms && (
                <div className="text-xs text-gray-500 mt-1">
                  P95 latency: {live.latency_p95_ms}ms
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Analogues Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                Analogues per Day (30d)
              </CardTitle>
              <CardDescription>Daily generation volume trend</CardDescription>
            </CardHeader>
            <CardContent>
              {analoguesTrendData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={analoguesTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="analogues" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  No data available yet
                </div>
              )}
            </CardContent>
          </Card>

          {/* Mod Group Mix */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-600" />
                Modification Strategy Mix (24h)
              </CardTitle>
              <CardDescription>Popular modification categories</CardDescription>
            </CardHeader>
            <CardContent>
              {modMixData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={modMixData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  No modifications selected yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Credits Flow Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-purple-600" />
              Credits Purchased vs Consumed (30d)
            </CardTitle>
            <CardDescription>Credit flow trends over time</CardDescription>
          </CardHeader>
          <CardContent>
            {creditsTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={creditsTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="purchased" 
                    stackId="1"
                    stroke="#8b5cf6" 
                    fill="#8b5cf6" 
                    fillOpacity={0.6}
                    name="Purchased"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="consumed" 
                    stackId="2"
                    stroke="#ef4444" 
                    fill="#ef4444" 
                    fillOpacity={0.6}
                    name="Consumed"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-80 flex items-center justify-center text-gray-400">
                No credit activity yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

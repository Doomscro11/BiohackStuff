// Analytics API helpers for Peptimancer Admin
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface LiveAnalytics {
  users_active_24h: number;
  analogues_24h: number;
  credits_purchased_24h: number;
  credits_consumed_24h: number;
  net_flow_24h: number;
  errors_24h: number;
  latency_p95_ms: number | null;
  mod_group_mix_24h: Record<string, number>;
}

export interface AnalyticsSnapshot {
  _id: string;
  snapshot_date: string;
  users_total: number;
  users_active_24h: number;
  analogues_24h: number;
  analogues_7d: number;
  analogues_total: number;
  credits_purchased_24h: number;
  credits_consumed_24h: number;
  net_flow_24h: number;
  mod_group_mix_24h: Record<string, number>;
  errors_24h: number;
  latency_p95_ms: number | null;
  created_at?: string;
}

export async function getLiveAnalytics() {
  const result = await fetchJSON<LiveAnalytics>(
    `${BACKEND_URL}/api/admin/analytics/live`,
    {
      credentials: 'include'
    }
  );
  return result;
}

export async function getSnapshots(days: number = 30) {
  const result = await fetchJSON<{ snapshots: AnalyticsSnapshot[]; count: number }>(
    `${BACKEND_URL}/api/admin/analytics/snapshots?days=${days}`,
    {
      credentials: 'include'
    }
  );
  return result;
}

// PatentPulse API helpers for Peptimancer Admin
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface PatentItem {
  _id;
  title;
  patent_id;
  assignee;
  country;
  expiry_date;
  status;
  keywords[];
  sequence_data | null;
  commercial_score;
  synthesis_score;
  fto_risk;
  repurpose_notes;
  created_at;
  updated_at;
  viability_score?;
}

export interface PatentStats {
  total;
  by_status: Record<string, number>;
  top_assignees: Array<{ assignee; count }>;
  avg_commercial_score;
  avg_synthesis_score;
  avg_fto_risk;
  expiring_soon_24mo;
}

export async function getPatentItems(filters?: {
  status?;
  country?;
  min_commercial_score?;
  limit?;
  skip?;
}) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status_filter', filters.status);
  if (filters?.country) params.append('country', filters.country);
  if (filters?.min_commercial_score !== undefined) {
    params.append('min_commercial_score', filters.min_commercial_score.toString());
  }
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.skip) params.append('skip', filters.skip.toString());
  
  const url = `${BACKEND_URL}/api/patentpulse/items${params.toString() ? '?' + params.toString() : ''}`;
  
  const result = await fetchJSON<{
    items: PatentItem[];
    count;
    total;
    skip;
    limit;
  }>(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  return result;
}

export async function getPatentStats() {
  const result = await fetchJSON<PatentStats>(
    `${BACKEND_URL}/api/patentpulse/stats`,
    {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );
  return result;
}

export async function getTopOpportunities(limit = 10) {
  const result = await fetchJSON<{
    opportunities: PatentItem[];
    count;
  }>(`${BACKEND_URL}/api/patentpulse/top-opportunities?limit=${limit}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  return result;
}

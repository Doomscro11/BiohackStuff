// PatentPulse API helpers for Peptimancer Admin
import { fetchJSON } from './http.ts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface PatentItem {
  _id: string;
  title: string;
  patent_id: string;
  assignee: string;
  country: string;
  expiry_date: string;
  status: string;
  keywords: string[];
  sequence_data: string | null;
  commercial_score: number;
  synthesis_score: number;
  fto_risk: number;
  repurpose_notes: string;
  created_at: string;
  updated_at: string;
  viability_score?: number;
}

export interface PatentStats {
  total: number;
  by_status: Record<string, number>;
  top_assignees: Array<{ assignee: string; count: number }>;
  avg_commercial_score: number;
  avg_synthesis_score: number;
  avg_fto_risk: number;
  expiring_soon_24mo: number;
}

export async function getPatentItems(filters?: {
  status?: string;
  country?: string;
  min_commercial_score?: number;
  limit?: number;
  skip?: number;
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
    count: number;
    total: number;
    skip: number;
    limit: number;
  }>(url);
  
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

export async function getTopOpportunities(limit: number = 10) {
  const result = await fetchJSON<{
    opportunities: PatentItem[];
    count: number;
  }>(`${BACKEND_URL}/api/patentpulse/top-opportunities?limit=${limit}`);
  return result;
}

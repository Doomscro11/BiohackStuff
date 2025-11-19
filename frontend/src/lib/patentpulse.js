// PatentPulse API helpers for Peptimancer Admin
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export async function getPatentItems(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.country) params.append('country', filters.country);
  
  const result = await fetchJSON(
    `${BACKEND_URL}/api/patentpulse/items?${params.toString()}`,
    { credentials: 'include' }
  );
  return result;
}

export async function getPatentStats() {
  const result = await fetchJSON(
    `${BACKEND_URL}/api/patentpulse/stats`,
    { credentials: 'include' }
  );
  return result;
}

export async function getTopOpportunities(limit = 10) {
  const result = await fetchJSON(
    `${BACKEND_URL}/api/patentpulse/opportunities?limit=${limit}`,
    { credentials: 'include' }
  );
  return result;
}

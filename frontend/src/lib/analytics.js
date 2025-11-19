// Analytics API helpers for Peptimancer Admin
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export async function getLiveAnalytics() {
  const result = await fetchJSON(
    `${BACKEND_URL}/api/admin/analytics/live`,
    {
      credentials: 'include'
    }
  );
  return result;
}

export async function getSnapshots(days = 30) {
  const result = await fetchJSON(
    `${BACKEND_URL}/api/admin/analytics/snapshots?days=${days}`,
    {
      credentials: 'include'
    }
  );
  return result;
}

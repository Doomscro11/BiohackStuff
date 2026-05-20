// Billing API Helpers for Peptimancer
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export async function fetchBillingState() {
  const result = await fetchJSON(`${BACKEND_URL}/api/billing/state`, {
    credentials: 'include'
  });
  return result;
}

export async function startCheckout(payload) {
  const result = await fetchJSON(`${BACKEND_URL}/api/billing/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  return result;
}

export async function getPlans() {
  const result = await fetchJSON(`${BACKEND_URL}/api/billing/admin/plans`, {
    credentials: 'include'
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch plans');
  }
  
  return result.data;
}

export async function upsertPlan(plan) {
  const result = await fetchJSON(`${BACKEND_URL}/api/billing/admin/plans`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(plan)
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to update plan');
  }
  
  return result.data;
}

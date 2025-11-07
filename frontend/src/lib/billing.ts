// Billing API Helpers for Peptimancer
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export async function fetchBillingState() {
  const response = await fetch(`${BACKEND_URL}/api/billing/state`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(await response.text() || 'Failed to fetch billing state');
  }
  
  return response.json();
}

export async function startCheckout(payload: {
  plan?: 'basic' | 'pro' | 'enterprise';
  purchase_credits?: number;
}) {
  const response = await fetch(`${BACKEND_URL}/api/billing/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    throw new Error(await response.text() || 'Failed to start checkout');
  }
  
  return response.json();
}

export async function getPlans() {
  const response = await fetch(`${BACKEND_URL}/api/billing/admin/plans`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(await response.text() || 'Failed to fetch plans');
  }
  
  return response.json();
}

export async function upsertPlan(plan: {
  code: string;
  price: number;
  credits: number;
}) {
  const response = await fetch(`${BACKEND_URL}/api/billing/admin/plans`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(plan)
  });
  
  if (!response.ok) {
    throw new Error(await response.text() || 'Failed to update plan');
  }
  
  return response.json();
}

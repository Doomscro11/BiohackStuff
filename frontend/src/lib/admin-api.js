// API utilities for Peptimancer Admin Panel
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface SettingsUpdate extends Partial<AdminSettings> {
  confirm;
}

// Admin API functions
export async function fetchAdminSettings() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings`);
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch settings');
  }
  return result.data;
}

export async function updateAdminSettings(payload: SettingsUpdate) {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to update settings');
  }
  
  return result.data;
}

export async function fetchSettingsHistory() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings/history`);
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch history');
  }
  return result.data;
}

export async function resetSettings() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to reset settings');
  }
  
  return result.data;
}

export async function exportSettings() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings/export`);
  if (!result.ok) {
    throw new Error(result.text || 'Failed to export settings');
  }
  return result.data;
}

// Public API functions
export async function fetchCurrentMode() {
  const result = await fetchJSON(`${BACKEND_URL}/api/mode`);
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch mode');
  }
  return result.data;
}
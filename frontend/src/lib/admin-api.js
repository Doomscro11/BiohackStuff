// API utilities for Peptimancer Admin Panel
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface SettingsUpdate extends Partial<AdminSettings> {
  confirm;
}

// Admin API functions
export async function fetchAdminSettings() {
  const response = await fetch(`${BACKEND_URL}/api/admin/settings`);
  if (!response.ok) {
    throw new Error(`Failed to fetch settings: ${response.statusText}`);
  }
  return response.json();
}

export async function updateAdminSettings(payload: SettingsUpdate) {
  const response = await fetch(`${BACKEND_URL}/api/admin/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to update settings');
  }
  
  return response.json();
}

export async function fetchSettingsHistory() {
  const response = await fetch(`${BACKEND_URL}/api/admin/settings/history`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }
  return response.json();
}

export async function resetSettings() {
  const response = await fetch(`${BACKEND_URL}/api/admin/settings/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to reset settings: ${response.statusText}`);
  }
  
  return response.json();
}

export async function exportSettings() {
  const response = await fetch(`${BACKEND_URL}/api/admin/settings/export`);
  if (!response.ok) {
    throw new Error(`Failed to export settings: ${response.statusText}`);
  }
  return response.json();
}

// Public API functions
export async function fetchCurrentMode() {
  const response = await fetch(`${BACKEND_URL}/api/mode`);
  if (!response.ok) {
    throw new Error(`Failed to fetch mode: ${response.statusText}`);
  }
  return response.json();
}
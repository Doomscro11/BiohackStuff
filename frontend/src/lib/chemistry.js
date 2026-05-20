// Chemistry utilities for Peptimancer - PK-aware options with tier gating
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Fetch canonical chemistry options from backend
 * Options are already filtered by user's tier
 */
export async function fetchChemistryOptions(): Promise<ChemistryOptions> {
  const result = await fetchJSON(`${BACKEND_URL}/api/chemistry/options`, {
    credentials: 'include' // Include JWT cookie
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch chemistry options');
  }
  
  return result.data;
}

/**
 * Client-side conflict awareness (UX hints only; server is authoritative)
 * Returns warning message if conflicts detected
 */
export function hasClientConflicts(mods, exclusions) {
  const set = new Set([...mods, ...exclusions]);
  
  // Mirror key UX conflicts (not exhaustive - server validates fully)
  if (set.has('pegylation') && set.has('lipidation') && set.has('no_linker_conflicts')) {
    return 'PEG + Lipidation is blocked by "No PEG + Lipidation combo" exclusion.';
  }
  
  if (set.has('acetylation') && set.has('lipidation')) {
    return 'N-acetylation and lipidation may conflict on the same residue.';
  }
  
  if (set.has('cyclization') && set.has('no_extra_cys')) {
    return 'Cyclization with "No extra Cys" may be incompatible.';
  }
  
  return null;
}

// Validation caps (must match backend constants)
export const MAX_MOD_CLASSES = 3;
export const MAX_EXCLUSIONS = 6;

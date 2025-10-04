const STORAGE_KEY = 'upstox_token_cache';

export interface TokenCacheEntry {
  token: string;
  expiresAt: string; // ISO string end of day IST
}

function storage(): Storage {
  try {
    return window.localStorage;
  } catch {
    return window.sessionStorage;
  }
}

export function saveUpstoxToken(token: string, expiresAt: string) {
  const entry: TokenCacheEntry = { token, expiresAt };
  storage().setItem(STORAGE_KEY, JSON.stringify(entry));
}

export function getUpstoxToken(): TokenCacheEntry | null {
  try {
    const raw = storage().getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as TokenCacheEntry;
  } catch {
    return null;
  }
}

export function clearUpstoxToken() {
  try { storage().removeItem(STORAGE_KEY); } catch {}
}

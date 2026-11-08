const SESSION_TOKEN_KEY = 'ipguard_session_access_token'

export function getStoredSessionToken(): string | null {
  try {
    return sessionStorage.getItem(SESSION_TOKEN_KEY)
  } catch {
    return null
  }
}

export function saveSessionToken(token: string): void {
  try {
    sessionStorage.setItem(SESSION_TOKEN_KEY, token)
  } catch {
    // Session storage not available or quota exceeded
  }
}

export function clearStoredSessionToken(): void {
  try {
    sessionStorage.removeItem(SESSION_TOKEN_KEY)
  } catch {
    // Session storage not available
  }
}

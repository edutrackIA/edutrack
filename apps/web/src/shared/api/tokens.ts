export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// Tokens are kept in sessionStorage: they survive page reloads (no refresh per reload)
// and are discarded when the browser closes, since school computers are often shared.
const ACCESS_KEY = 'edutrack.access_token'
const REFRESH_KEY = 'edutrack.refresh_token'

let accessToken: string | null = null

export function getAccessToken(): string | null {
  if (accessToken === null) {
    try {
      accessToken = sessionStorage.getItem(ACCESS_KEY)
    } catch {
      return null
    }
  }
  return accessToken
}

export function getRefreshToken(): string | null {
  try {
    return sessionStorage.getItem(REFRESH_KEY)
  } catch {
    return null
  }
}

export function setTokens(tokens: TokenPair): void {
  accessToken = tokens.access_token
  try {
    sessionStorage.setItem(ACCESS_KEY, tokens.access_token)
    sessionStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  } catch {
    /* storage unavailable: the session lasts until the page reloads */
  }
}

export function clearTokens(): void {
  accessToken = null
  try {
    sessionStorage.removeItem(ACCESS_KEY)
    sessionStorage.removeItem(REFRESH_KEY)
  } catch {
    /* storage unavailable */
  }
}

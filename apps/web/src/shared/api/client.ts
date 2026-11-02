import { clearTokens, getAccessToken, getRefreshToken, setTokens, type TokenPair } from './tokens'

const BASE_URL = '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  auth?: boolean
  signal?: AbortSignal
}

const expiredListeners = new Set<() => void>()
let refreshing: Promise<boolean> | null = null

export function onSessionExpired(listener: () => void): () => void {
  expiredListeners.add(listener)
  return () => {
    expiredListeners.delete(listener)
  }
}

/** Rotates the tokens once, even if several requests fail with 401 at the same time. */
export function refreshSession(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return Promise.resolve(false)

  refreshing ??= (async () => {
    try {
      const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) return false
      setTokens((await response.json()) as TokenPair)
      return true
    } catch {
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

function send(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  let body: BodyInit | undefined
  if (options.body instanceof FormData) {
    body = options.body
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }
  const token = getAccessToken()
  if (options.auth !== false && token) headers.Authorization = `Bearer ${token}`

  return fetch(`${BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body,
    signal: options.signal,
  })
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = response.status === 422 ? 'VALIDATION_ERROR' : 'HTTP_ERROR'
  let message = `La solicitud falló (${response.status}).`
  try {
    const data = (await response.json()) as { code?: unknown; message?: unknown }
    if (typeof data.code === 'string') code = data.code
    if (typeof data.message === 'string') message = data.message
  } catch {
    /* response without a JSON body */
  }
  return new ApiError(response.status, code, message)
}

/** Low-level request: handles the token, one refresh retry and API errors. */
export async function apiFetch(path: string, options: RequestOptions = {}): Promise<Response> {
  let response = await send(path, options)

  if (response.status === 401 && options.auth !== false && getRefreshToken()) {
    if (await refreshSession()) {
      response = await send(path, options)
    } else {
      clearTokens()
      expiredListeners.forEach((listener) => listener())
    }
  }

  if (!response.ok) throw await toApiError(response)
  return response
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await apiFetch(path, options)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

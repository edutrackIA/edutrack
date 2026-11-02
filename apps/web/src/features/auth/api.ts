import { apiRequest } from '../../shared/api/client'
import type { TokenPair } from '../../shared/api/tokens'
import type { User } from './types'

export function loginRequest(email: string, password: string): Promise<TokenPair> {
  return apiRequest<TokenPair>('/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,
  })
}

export function fetchMe(): Promise<User> {
  return apiRequest<User>('/auth/me')
}

export function logoutRequest(refreshToken: string): Promise<void> {
  return apiRequest<void>('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  })
}

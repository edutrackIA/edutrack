import { describe, expect, it, vi } from 'vitest'
import { json, mockApi, TOKENS } from '../../test/server'
import { ApiError, apiRequest, onSessionExpired } from './client'
import { getRefreshToken, setTokens } from './tokens'

describe('apiRequest', () => {
  it('sends the access token', async () => {
    setTokens(TOKENS)
    const fetchMock = mockApi({ 'GET /auth/me': () => json({ id: 1 }) })

    await apiRequest('/auth/me')

    const headers = fetchMock.mock.calls[0][1]?.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer access-1')
  })

  it('refreshes the session once and retries after a 401', async () => {
    setTokens(TOKENS)
    let calls = 0
    const fetchMock = mockApi({
      'GET /classrooms': () => (++calls === 1 ? json({ code: 'UNAUTHORIZED' }, 401) : json([])),
      'POST /auth/refresh': () =>
        json({ ...TOKENS, access_token: 'access-2', refresh_token: 'refresh-2' }),
    })

    await expect(apiRequest('/classrooms')).resolves.toEqual([])

    const retryHeaders = fetchMock.mock.calls[2][1]?.headers as Record<string, string>
    expect(retryHeaders.Authorization).toBe('Bearer access-2')
    expect(getRefreshToken()).toBe('refresh-2')
  })

  it('ends the session when the refresh fails', async () => {
    setTokens(TOKENS)
    const expired = vi.fn()
    const unsubscribe = onSessionExpired(expired)
    mockApi({
      'GET /classrooms': () => json({ code: 'UNAUTHORIZED', message: 'Expired' }, 401),
      'POST /auth/refresh': () => json({ code: 'INVALID_REFRESH_TOKEN' }, 401),
    })

    await expect(apiRequest('/classrooms')).rejects.toMatchObject({ status: 401 })

    expect(expired).toHaveBeenCalledOnce()
    expect(getRefreshToken()).toBeNull()
    unsubscribe()
  })

  it('maps API errors and validation errors', async () => {
    mockApi({
      'POST /settings': () => json({ code: 'FORBIDDEN', message: 'No access' }, 403),
      'PUT /settings': () => json({ detail: [{ msg: 'bad' }] }, 422),
    })

    const forbidden = await apiRequest('/settings', { method: 'POST' }).catch((e: unknown) => e)
    const invalid = await apiRequest('/settings', { method: 'PUT' }).catch((e: unknown) => e)

    expect(forbidden).toBeInstanceOf(ApiError)
    expect(forbidden).toMatchObject({ status: 403, code: 'FORBIDDEN' })
    expect(invalid).toMatchObject({ status: 422, code: 'VALIDATION_ERROR' })
  })
})

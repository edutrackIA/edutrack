import { describe, expect, it } from 'vitest'
import { ApiError } from './client'
import { messageFor } from './errors'

describe('messageFor', () => {
  it('explains a temporary block after too many failed attempts', () => {
    const error = new ApiError(429, 'TOO_MANY_ATTEMPTS', 'Too many failed login attempts')

    expect(messageFor(error)).toMatch(/espera unos minutos/)
  })

  it('falls back to the server message for unknown codes', () => {
    expect(messageFor(new ApiError(422, 'SOMETHING_NEW', 'Mensaje del servidor'))).toBe(
      'Mensaje del servidor',
    )
  })

  it('explains connection problems', () => {
    expect(messageFor(new TypeError('Failed to fetch'))).toMatch(/No pudimos conectar/)
  })
})

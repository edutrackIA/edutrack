import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the API as online when the health check succeeds', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))

    render(<App />)

    expect(screen.getByRole('heading', { name: 'EduTrack' })).toBeInTheDocument()
    expect(await screen.findByText('API: online')).toBeInTheDocument()
  })

  it('shows the API as offline when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')))

    render(<App />)

    expect(await screen.findByText('API: offline')).toBeInTheDocument()
  })
})

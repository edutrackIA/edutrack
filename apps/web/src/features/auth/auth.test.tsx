import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { createQueryClient } from '../../app/query-client'
import { routes } from '../../app/routes'
import { setTokens } from '../../shared/api/tokens'
import { renderApp } from '../../test/render'
import { AuthProvider } from './AuthProvider'
import { json, mockApi, TOKENS } from '../../test/server'

const TEACHER = {
  id: 2,
  email: 'docente@edutrack.dev',
  full_name: 'Luis Quispe',
  role: 'TEACHER',
  institution_id: 1,
}
const PARENT = { ...TEACHER, id: 4, full_name: 'Rosa Huamán', role: 'PARENT' }

describe('authentication', () => {
  it('redirects anonymous visitors to the login page', async () => {
    mockApi({})

    const router = renderApp('/aulas')

    expect(await screen.findByRole('heading', { name: 'Inicia sesión' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
  })

  it('logs in and opens the home page of the role', async () => {
    mockApi({
      'POST /auth/login': () => json(TOKENS),
      'GET /auth/me': () => json(TEACHER),
      'GET /classrooms': () => json([]),
      'GET /alerts': () => json({ total: 0, items: [] }),
    })
    const router = renderApp('/login')
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('Correo'), 'docente@edutrack.dev')
    await user.type(screen.getByLabelText('Contraseña'), 'Edutrack123!')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByRole('heading', { name: 'Mis aulas' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/aulas')
    expect(screen.getByRole('link', { name: 'Alertas' })).toBeInTheDocument()
    expect(screen.getByText('Luis Quispe')).toBeInTheDocument()
  })

  it('explains wrong credentials in plain language', async () => {
    mockApi({
      'POST /auth/login': () =>
        json({ code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' }, 401),
    })
    renderApp('/login')
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('Correo'), 'docente@edutrack.dev')
    await user.type(screen.getByLabelText('Contraseña'), 'incorrecta')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'El correo o la contraseña no son correctos.',
    )
  })

  it('restores the session from the stored refresh token', async () => {
    setTokens(TOKENS)
    mockApi({
      'POST /auth/refresh': () => json({ ...TOKENS, refresh_token: 'refresh-2' }),
      'GET /auth/me': () => json(PARENT),
    })

    const router = renderApp('/')

    expect(await screen.findByRole('heading', { name: 'Mi hijo' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/mi-hijo')
  })

  it('explains on the login page that the session expired', async () => {
    setTokens(TOKENS)
    mockApi({
      'GET /auth/me': () => json({ code: 'UNAUTHORIZED', message: 'Expired' }, 401),
      'POST /auth/refresh': () => json({ code: 'INVALID_REFRESH_TOKEN' }, 401),
    })

    const router = renderApp('/aulas')

    expect(await screen.findByText(/Tu sesión expiró/)).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
  })

  it('blocks sections that do not belong to the role', async () => {
    setTokens(TOKENS)
    mockApi({
      'POST /auth/refresh': () => json(TOKENS),
      'GET /auth/me': () => json(PARENT),
    })

    renderApp('/resumen')

    expect(await screen.findByText('No tienes acceso a esta sección')).toBeInTheDocument()
  })

  it('logs out and returns to the login page', async () => {
    setTokens(TOKENS)
    mockApi({
      'POST /auth/refresh': () => json(TOKENS),
      'GET /auth/me': () => json(TEACHER),
      'GET /classrooms': () => json([]),
      'GET /alerts': () => json({ total: 0, items: [] }),
      'POST /auth/logout': () => new Response(null, { status: 204 }),
    })
    const router = renderApp('/aulas')
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Cerrar sesión' }))

    expect(await screen.findByRole('heading', { name: 'Inicia sesión' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
  })
})

describe('session safety', () => {
  it('reloads with a stored access token without rotating the refresh token', async () => {
    setTokens(TOKENS)
    const fetchMock = mockApi({
      'GET /auth/me': () => json(TEACHER),
      'GET /classrooms': () => json([]),
      'GET /alerts': () => json({ total: 0, items: [] }),
    })

    renderApp('/aulas')

    expect(await screen.findByRole('heading', { name: 'Mis aulas' })).toBeInTheDocument()
    const urls = fetchMock.mock.calls.map(([url]) => String(url))
    expect(urls).toContain('/api/v1/auth/me')
    expect(urls).not.toContain('/api/v1/auth/refresh')
  })

  it('ignores redirects to other sites after login', async () => {
    mockApi({
      'POST /auth/login': () => json(TOKENS),
      'GET /auth/me': () => json(TEACHER),
      'GET /classrooms': () => json([]),
      'GET /alerts': () => json({ total: 0, items: [] }),
    })
    const router = createMemoryRouter(routes, {
      initialEntries: [{ pathname: '/login', state: { from: '/\\evil.example' } }],
    })
    render(
      <QueryClientProvider client={createQueryClient()}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </QueryClientProvider>,
    )
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('Correo'), 'docente@edutrack.dev')
    await user.type(screen.getByLabelText('Contraseña'), 'Edutrack123!')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByRole('heading', { name: 'Mis aulas' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/aulas')
  })
})

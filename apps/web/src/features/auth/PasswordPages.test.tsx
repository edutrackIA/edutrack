import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import AccountPage from './pages/AccountPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'

describe('ForgotPasswordPage', () => {
  it('confirms the request without revealing whether the email exists', async () => {
    const bodies: unknown[] = []
    mockApi({
      'POST /auth/password/forgot': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json(null, 202)
      },
    })
    renderPage(<ForgotPasswordPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Correo'), 'rosa@correo.com')
    await user.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    expect(await screen.findByText(/Si rosa@correo.com está registrado/)).toBeInTheDocument()
    expect(bodies).toEqual([{ email: 'rosa@correo.com' }])
  })
})

describe('ResetPasswordPage', () => {
  const ROUTE = { route: '/restablecer/:token', path: '/restablecer/abc' }

  it('saves a new password that meets the rules', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /auth/password/reset/abc': () => json({ email: 'rosa@correo.com' }),
      'POST /auth/password/reset/abc': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return new Response(null, { status: 204 })
      },
    })
    renderPage(<ResetPasswordPage />, ROUTE)
    const user = userEvent.setup()

    expect(await screen.findByText('Para rosa@correo.com.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Nueva contraseña'), 'Clave2026')
    await user.type(screen.getByLabelText('Repite la contraseña'), 'Clave2026')
    await user.click(screen.getByRole('button', { name: 'Guardar contraseña' }))

    expect(await screen.findByRole('heading', { name: 'Contraseña actualizada' })).toBeInTheDocument()
    expect(bodies).toEqual([{ password: 'Clave2026' }])
  })

  it('offers a new link when this one expired', async () => {
    mockApi({
      'GET /auth/password/reset/abc': () =>
        json({ code: 'INVITATION_EXPIRED', message: 'Expired' }, 409),
    })

    renderPage(<ResetPasswordPage />, ROUTE)

    expect(await screen.findByRole('heading', { name: 'Enlace no válido' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Pedir otro enlace' })).toHaveAttribute('href', '/recuperar')
  })
})

describe('AccountPage', () => {
  it('changes the password with the current one', async () => {
    const bodies: unknown[] = []
    mockApi({
      'POST /auth/password/change': (init) => {
        const body = JSON.parse(String(init?.body))
        bodies.push(body)
        return body.current_password === 'Edutrack123!'
          ? new Response(null, { status: 204 })
          : json({ code: 'WRONG_PASSWORD', message: 'Wrong' }, 422)
      },
    })
    renderPage(<AccountPage />, { user: TEACHER_USER })
    const user = userEvent.setup()

    expect(screen.getByText('docente@edutrack.dev')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Contraseña actual'), 'Equivocada1')
    await user.type(screen.getByLabelText('Nueva contraseña'), 'NuevaClave2026')
    await user.type(screen.getByLabelText('Repite la contraseña'), 'NuevaClave2026')
    await user.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('La contraseña actual no es correcta.')

    await user.clear(screen.getByLabelText('Contraseña actual'))
    await user.type(screen.getByLabelText('Contraseña actual'), 'Edutrack123!')
    await user.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(2))
    expect(bodies[1]).toEqual({ current_password: 'Edutrack123!', new_password: 'NuevaClave2026' })
  })
})

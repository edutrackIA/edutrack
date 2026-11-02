import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import AcceptInvitationPage from './pages/AcceptInvitationPage'

const ROUTE = { route: '/invitacion/:token', path: '/invitacion/tok123' }

describe('AcceptInvitationPage', () => {
  it('lets the guardian create a password that meets every rule', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /invitations/tok123': () => json({ full_name: 'Rosa Huamán', email: 'rosa@correo.com' }),
      'POST /invitations/tok123/accept': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return new Response(null, { status: 204 })
      },
    })
    renderPage(<AcceptInvitationPage />, ROUTE)
    const user = userEvent.setup()

    expect(await screen.findByRole('heading', { name: 'Hola, Rosa' })).toBeInTheDocument()
    const submit = screen.getByRole('button', { name: 'Crear contraseña' })
    await user.type(screen.getByLabelText('Contraseña'), 'clave')
    expect(submit).toBeDisabled()
    expect(screen.getByText(/Al menos un número/)).toHaveTextContent('pendiente')

    await user.type(screen.getByLabelText('Contraseña'), '2026')
    await user.type(screen.getByLabelText('Repite la contraseña'), 'clave2026')
    await user.click(submit)

    expect(await screen.findByRole('heading', { name: 'Tu contraseña está lista' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Iniciar sesión' })).toHaveAttribute('href', '/login')
    expect(bodies).toEqual([{ password: 'clave2026' }])
  })

  it('explains when the link expired or was already used', async () => {
    mockApi({
      'GET /invitations/tok123': () =>
        json({ code: 'INVITATION_EXPIRED', message: 'No longer valid' }, 409),
    })

    renderPage(<AcceptInvitationPage />, ROUTE)

    expect(await screen.findByRole('heading', { name: 'Enlace no válido' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Pide al colegio que te envíe uno nuevo')
  })
})

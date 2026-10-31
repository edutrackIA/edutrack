import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { User } from '../auth/types'
import { DIRECTOR_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import { ConsentGate } from './components/ConsentGate'
import { MyDataRequests } from './components/MyDataRequests'
import DataRequestsPage from './pages/DataRequestsPage'

const PARENT: User = {
  id: 4,
  email: 'padre@edutrack.dev',
  full_name: 'Rosa Huamán',
  role: 'PARENT',
  institution_id: 1,
}

const REQUEST = {
  id: 3,
  student_id: 1,
  student_name: 'Huamán Flores, Lucía',
  requester_name: 'Rosa Huamán',
  kind: 'ACCESS',
  details: 'Quiero una copia de todos los datos de mi hija.',
  status: 'PENDING',
  response: null,
  created_at: '2026-11-02T10:00:00',
  due_date: '2100-12-01',
  resolved_at: null,
}

describe('ConsentGate', () => {
  it('asks guardians to accept the notice before showing the portal', async () => {
    const versions: string[] = []
    mockApi({
      'GET /me/privacy': () => json({ version: '2026-11', accepted_at: null }),
      'POST /me/privacy/acceptance': (init) => {
        versions.push(JSON.parse(String(init?.body)).version)
        return json({ version: '2026-11', accepted_at: '2026-11-02T10:00:00' })
      },
    })
    renderPage(
      <ConsentGate>
        <p>Portal de la familia</p>
      </ConsentGate>,
      { user: PARENT },
    )
    const user = userEvent.setup()

    expect(await screen.findByRole('heading', { name: 'Antes de empezar' })).toBeInTheDocument()
    expect(screen.queryByText('Portal de la familia')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Acepto' })).toBeDisabled()

    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Acepto' }))

    expect(await screen.findByText('Portal de la familia')).toBeInTheDocument()
    expect(versions).toEqual(['2026-11'])
  })

  it('does not ask staff for consent', () => {
    renderPage(
      <ConsentGate>
        <p>Resumen</p>
      </ConsentGate>,
      { user: DIRECTOR_USER },
    )

    expect(screen.getByText('Resumen')).toBeInTheDocument()
  })
})

describe('MyDataRequests', () => {
  it('sends an access request about a child', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /me/children': () =>
        json([{ id: 1, code: '20260001', full_name: 'Huamán Flores, Lucía', classroom: '3° A', risk_level: null, probability: null }]),
      'GET /data-requests': () => json([]),
      'POST /data-requests': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json(REQUEST, 201)
      },
    })
    renderPage(<MyDataRequests />, { user: PARENT })
    const user = userEvent.setup()

    await screen.findByRole('option', { name: 'Lucía' })
    await user.type(screen.getByLabelText('Detalle'), 'Quiero una copia de todos los datos de mi hija.')
    await user.click(screen.getByRole('button', { name: 'Enviar solicitud' }))

    expect(await screen.findByText(/Solicitud enviada/)).toBeInTheDocument()
    expect(bodies).toEqual([
      { student_id: 1, kind: 'ACCESS', details: 'Quiero una copia de todos los datos de mi hija.' },
    ])
  })
})

describe('DataRequestsPage', () => {
  it('lets direction answer a pending request', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /data-requests': () => json([REQUEST]),
      'POST /data-requests/3/resolution': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ ...REQUEST, status: 'RESOLVED' })
      },
    })
    renderPage(<DataRequestsPage />, { user: DIRECTOR_USER })
    const user = userEvent.setup()

    expect(await screen.findByText(/Responder hasta el/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /^Responder la solicitud/ }))
    await user.type(
      await screen.findByLabelText('Respuesta para la familia'),
      'Le enviamos el expediente por correo.',
    )
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))

    await vi.waitFor(() =>
      expect(bodies).toEqual([{ status: 'RESOLVED', response: 'Le enviamos el expediente por correo.' }]),
    )
  })
})

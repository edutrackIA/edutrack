import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { User } from '../auth/types'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import ParentPortalPage from './pages/ParentPortalPage'

const PARENT: User = {
  id: 4,
  email: 'padre@edutrack.dev',
  full_name: 'Rosa Huamán',
  role: 'PARENT',
  institution_id: 1,
}

const CHILD = {
  id: 1,
  code: '20260001',
  full_name: 'Huamán Flores, Lucía',
  classroom: '3° A',
  risk_level: null,
  probability: null,
}

const SUMMARY = {
  period_id: 3,
  average_score: 12.5,
  attendance_rate: 0.92,
  grades: [
    { subject_id: 1, subject: 'Matemática', period_id: 3, score: 9 },
    { subject_id: 2, subject: 'Comunicación', period_id: 3, score: 15 },
  ],
  parent_suggestions: ['Matemática: practicar 15 minutos diarios de ejercicios cortos.'],
  disclaimer: 'Estas recomendaciones fueron generadas automáticamente por EduTrack.',
}

const PERIOD = {
  id: 3,
  year: 2026,
  bimester: 3,
  start_date: '2000-01-01',
  end_date: '2100-12-31',
  label: 'Bimestre 3, 2026',
}

function mockPortal(overrides: Record<string, (init?: RequestInit) => Response> = {}) {
  return mockApi({
    'GET /me/children': () => json([CHILD]),
    'GET /students/1/summary': () => json(SUMMARY),
    'GET /students/1/family-checkins/current': () => json({ month: '2026-10-01', checkin: null }),
    'GET /students/1/surveys': () => json([]),
    'GET /students/1/commitments': () => json([]),
    'GET /periods': () => json([PERIOD]),
    ...overrides,
  })
}

describe('ParentPortalPage', () => {
  it('shows the progress and the approved suggestions without risk levels', async () => {
    mockPortal()

    renderPage(<ParentPortalPage />, { user: PARENT })

    expect(await screen.findByRole('heading', { name: 'Avance de Lucía' })).toBeInTheDocument()
    expect(await screen.findByText(/practicar 15 minutos diarios/)).toBeInTheDocument()
    expect(screen.getByText(/generadas automáticamente por EduTrack/)).toBeInTheDocument()
    expect(screen.getByText('(desaprobado)', { exact: false })).toBeInTheDocument()
    expect(screen.queryByText(/riesgo/i)).not.toBeInTheDocument()
  })

  it('sends the monthly follow-up, including a concern about classmates', async () => {
    const bodies: unknown[] = []
    mockPortal({
      'PUT /students/1/family-checkins/current': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ id: 1 })
      },
    })
    renderPage(<ParentPortalPage />, { user: PARENT })
    const user = userEvent.setup()

    await user.click(await screen.findByLabelText('Nos preocupa'))
    await user.click(screen.getByLabelText('Mudanza'))
    await user.click(screen.getByLabelText(/Me preocupa cómo lo tratan sus compañeros/))
    await user.type(screen.getByLabelText('Comentario para el tutor (opcional)'), 'Llega triste.')
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))

    expect(await screen.findByText('Gracias. El tutor recibió su respuesta de octubre.')).toBeInTheDocument()
    expect(bodies).toEqual([
      { mood: 'WORRIED', home_changes: ['MOVING'], peer_concern: true, comment: 'Llega triste.' },
    ])
  })

  it('keeps the confirmation after the first answer of the month is saved', async () => {
    let saved: Record<string, unknown> | null = null
    mockPortal({
      // Once saved, the server returns the follow-up with its id, as in production.
      'GET /students/1/family-checkins/current': () =>
        json({ month: '2026-10-01', checkin: saved }),
      'PUT /students/1/family-checkins/current': (init) => {
        saved = { id: 7, month: '2026-10-01', ...JSON.parse(String(init?.body)) }
        return json(saved)
      },
    })
    renderPage(<ParentPortalPage />, { user: PARENT })
    const user = userEvent.setup()

    await user.click(await screen.findByLabelText('Lo vemos bien'))
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))

    expect(await screen.findByRole('button', { name: 'Actualizar respuesta' })).toBeInTheDocument()
    expect(screen.getByText('Gracias. El tutor recibió su respuesta de octubre.')).toBeInTheDocument()
  })

  it('asks for the family survey of the current period', async () => {
    const bodies: unknown[] = []
    mockPortal({
      'POST /students/1/surveys': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ id: 1 }, 201)
      },
    })
    renderPage(<ParentPortalPage />, { user: PARENT })
    const user = userEvent.setup()

    await user.selectOptions(await screen.findByLabelText('¿Tiene un dispositivo para estudiar?'), 'no')
    await user.click(screen.getByRole('button', { name: 'Enviar encuesta' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(1))
    expect(bodies[0]).toMatchObject({ period_id: 3, has_study_device: false, home_internet: true })
  })

  it('explains when no child is linked to the account', async () => {
    mockApi({ 'GET /me/children': () => json([]) })

    renderPage(<ParentPortalPage />, { user: PARENT })

    expect(await screen.findByText('Aún no hay estudiantes vinculados a su cuenta')).toBeInTheDocument()
  })
})

import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import DashboardPage from '../dashboard/pages/DashboardPage'

const PERIODS = [
  { id: 3, year: 2026, bimester: 3, start_date: '2026-08-03', end_date: '2026-10-02', label: 'Bimestre 3, 2026' },
]

const SUMMARY = {
  period_id: 3,
  period_label: '2026 · Bimestre 3',
  total_students: 2,
  evaluated_students: 2,
  by_level: { LOW: 1, MEDIUM: 0, HIGH: 1 },
  by_classroom: [{ classroom_id: 1, label: '3° A', evaluated: 2, low: 1, medium: 0, high: 1 }],
  top_factors: [{ feature: 'attendance_rate', label: 'Asistencia', frequency: 1 }],
  students: [
    {
      student_id: 6,
      code: '20260006',
      full_name: 'Ramírez Gutiérrez, Lucía',
      classroom_id: 1,
      classroom: '3° A',
      level: 'HIGH',
      probability: 0.94,
    },
  ],
}

const STUDENT = {
  id: 6,
  code: '20260006',
  first_name: 'Lucía',
  last_name: 'Ramírez Gutiérrez',
  birth_date: '2012-04-10',
  sex: 'F',
  classroom_id: 1,
  guardians: [
    { id: 4, email: 'padre@edutrack.dev', full_name: 'Rosa Huamán', role: 'PARENT', institution_id: 1 },
  ],
  latest_risk: {
    id: 1,
    period_id: 3,
    probability: 0.94,
    level: 'HIGH',
    model_version: 'rf-test',
    top_factors: [
      { feature: 'attendance_rate', label: 'Asistencia', value: 0.78, contribution: 0.31 },
      { feature: 'failed_subjects', label: 'Cursos desaprobados', value: 2, contribution: 0.2 },
    ],
    created_at: '2026-10-25T00:00:00',
  },
}

const STUDENT_SUMMARY = {
  period_id: 3,
  average_score: 9.8,
  attendance_rate: 0.78,
  grades: [
    { subject_id: 1, subject: 'Matemática', period_id: 3, score: 8 },
    { subject_id: 2, subject: 'Comunicación', period_id: 3, score: 12.5 },
  ],
}

function mockDashboard() {
  return mockApi({
    'GET /dashboard/summary': () => json(SUMMARY),
    'GET /periods': () => json(PERIODS),
    'GET /students/6': () => json(STUDENT),
    'GET /students/6/summary': () => json(STUDENT_SUMMARY),
    'GET /students/6/recommendations': () =>
      json([{ id: 9, period_id: 3, status: 'PENDING_REVIEW', sent_at: null, created_at: '2026-10-25' }]),
  })
}

describe('StudentQuickView', () => {
  it('opens the student in a modal from the traffic light', async () => {
    const fetchMock = mockDashboard()
    renderPage(<DashboardPage />)
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: /Ramírez Gutiérrez, Lucía/ }))

    const dialog = await screen.findByRole('dialog', { name: 'Ramírez Gutiérrez, Lucía' })
    expect(within(dialog).getByText('3° A, código 20260006')).toBeInTheDocument()
    expect(await within(dialog).findByText(/de probabilidad/)).toBeInTheDocument()
    expect(within(dialog).getByRole('list', { name: 'Qué explica el riesgo' })).toHaveTextContent(
      'Cursos desaprobados',
    )
    expect(within(dialog).getByRole('list', { name: 'Notas del bimestre' })).toHaveTextContent(
      'Matemática',
    )
    expect(within(dialog).getByText('(desaprobado)', { exact: false })).toBeInTheDocument()
    expect(within(dialog).getByText('Rosa Huamán')).toBeInTheDocument()
    expect(within(dialog).getByText('Pendiente de revisión del tutor')).toBeInTheDocument()
    expect(fetchMock.mock.calls.map(([url]) => String(url))).toContain(
      '/api/v1/students/6/summary?period_id=3',
    )
  })

  it('closes with the close button', async () => {
    mockDashboard()
    renderPage(<DashboardPage />)
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: /Ramírez Gutiérrez, Lucía/ }))
    const dialog = await screen.findByRole('dialog', { name: 'Ramírez Gutiérrez, Lucía' })

    await user.click(within(dialog).getByRole('button', { name: 'Cerrar' }))

    expect(dialog).not.toHaveAttribute('open')
  })
})

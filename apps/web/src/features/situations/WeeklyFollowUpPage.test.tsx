import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DIRECTOR_USER, TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import WeeklyFollowUpPage from './pages/WeeklyFollowUpPage'

const CLASSROOMS = [{ id: 1, year: 2026, grade: 3, section: 'A', tutor: TEACHER_USER, student_count: 2 }]
const STUDENTS = [
  { id: 6, code: '20260006', full_name: 'Ramírez Gutiérrez, Lucía', classroom: '3° A', risk_level: 'HIGH', probability: 0.9 },
  { id: 1, code: '20260001', full_name: 'Castillo, Mateo', classroom: '3° A', risk_level: 'LOW', probability: 0.1 },
]
const CATALOG = [
  { kind: 'GRIEF', label: 'Duelo familiar', group: 'MESSAGE', description: 'Pérdida de un familiar.' },
  { kind: 'BULLYING', label: 'Convivencia escolar (posible acoso)', group: 'TEAM', description: 'Activa el protocolo.' },
]
const GRIEF = {
  id: 3,
  student_id: 1,
  kind: 'GRIEF',
  label: 'Duelo familiar',
  group: 'MESSAGE',
  note: null,
  started_on: '2026-10-20',
  resolved_on: null,
  created_at: '2026-10-20T10:00:00',
}
const PENDING = {
  classroom_id: 1,
  week_start: '2026-10-26',
  deadline: '2026-10-31',
  editable: true,
  completed: false,
  completed_at: null,
}

describe('WeeklyFollowUpPage', () => {
  it('marks a team-only situation and confirms the week', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /classrooms': () => json(CLASSROOMS),
      'GET /classrooms/1/checkins/current': () => json(PENDING),
      'GET /classrooms/1/students': () => json(STUDENTS),
      'GET /classrooms/1/situations': () => json([GRIEF]),
      'GET /situations/catalog': () => json(CATALOG),
      'POST /students/6/situations': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ ...GRIEF, id: 4, student_id: 6, kind: 'BULLYING', group: 'TEAM' }, 201)
      },
      'POST /classrooms/1/checkins/current/complete': () =>
        json({ ...PENDING, completed: true, completed_at: '2026-10-28T15:00:00' }),
    })
    renderPage(<WeeklyFollowUpPage />, { user: TEACHER_USER })
    const user = userEvent.setup()

    expect(await screen.findByText(/Pendiente\. Tienes hasta el/)).toBeInTheDocument()
    const table = screen.getByRole('table', { name: 'Situaciones de los estudiantes de 3° A' })
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows.map((row) => within(row).getAllByRole('cell')[0].textContent)).toEqual([
      'Castillo, Mateo',
      'Ramírez Gutiérrez, Lucía',
    ])
    expect(within(rows[0]).getByRole('button', { name: /Duelo familiar/ })).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: 'Marcar situación de Ramírez Gutiérrez, Lucía' }),
    )
    const dialog = await screen.findByRole('dialog', { name: 'Marcar una situación' })
    await user.selectOptions(within(dialog).getByLabelText('Situación'), 'BULLYING')
    expect(within(dialog).getByText(/La familia no verá esta situación/)).toBeInTheDocument()
    await user.type(within(dialog).getByLabelText('Nota para el equipo'), 'Lo molestan en el recreo.')
    await user.click(within(dialog).getByRole('button', { name: 'Guardar situación' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(1))
    expect(bodies[0]).toMatchObject({ kind: 'BULLYING', note: 'Lo molestan en el recreo.' })

    await user.click(screen.getByRole('button', { name: 'Confirmar seguimiento de la semana' }))
    expect(await screen.findByText(/Completado\./)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Volver a confirmar la semana' })).toBeInTheDocument()
  })

  it('tells teachers who are not tutors that the follow-up is not theirs', async () => {
    mockApi({
      'GET /classrooms': () => json([{ ...CLASSROOMS[0], tutor: DIRECTOR_USER }]),
    })

    renderPage(<WeeklyFollowUpPage />, { user: TEACHER_USER })

    expect(await screen.findByText('No eres tutor de ninguna aula')).toBeInTheDocument()
  })

  it('disables the confirmation once the week is closed', async () => {
    mockApi({
      'GET /classrooms': () => json(CLASSROOMS),
      'GET /classrooms/1/checkins/current': () => json({ ...PENDING, editable: false }),
      'GET /classrooms/1/students': () => json(STUDENTS),
      'GET /classrooms/1/situations': () => json([]),
    })

    renderPage(<WeeklyFollowUpPage />, { user: TEACHER_USER })

    expect(await screen.findByText(/La semana ya cerró/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar seguimiento de la semana' })).toBeDisabled()
  })
})

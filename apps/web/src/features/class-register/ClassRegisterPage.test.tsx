import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import ClassRegisterPage from './pages/ClassRegisterPage'

const TEACHING = {
  courses: [{ classroom_id: 1, classroom: '3° A', year: 2026, subject_id: 2, subject: 'Matemática' }],
  classrooms: [{ classroom_id: 1, classroom: '3° A', year: 2026, is_tutor: true }],
}
const STUDENTS = [
  { student_id: 6, code: '20260006', full_name: 'Castillo, Mateo' },
  { student_id: 7, code: '20260007', full_name: 'Flores, Lucía' },
]
const PERIODS = [
  { id: 3, year: 2026, bimester: 3, start_date: '2000-01-01', end_date: '2100-12-31', label: 'Bimestre 3, 2026', has_grades: true },
]

describe('ClassRegisterPage', () => {
  it('takes attendance marking the rest as present', async () => {
    const bodies: { date: string; records: unknown[] }[] = []
    mockApi({
      'GET /me/teaching': () => json(TEACHING),
      'GET /classrooms/1/attendance': () =>
        json({ classroom_id: 1, date: '2026-10-28', period_id: 3, rows: STUDENTS.map((s) => ({ ...s, status: null })) }),
      'PUT /classrooms/1/attendance': (init) => {
        const body = JSON.parse(String(init?.body))
        bodies.push(body)
        return json({ classroom_id: 1, date: body.date, period_id: 3, rows: STUDENTS.map((s) => ({ ...s, status: 'PRESENT' })) })
      },
    })
    renderPage(<ClassRegisterPage />, { user: TEACHER_USER })
    const user = userEvent.setup()

    const mateo = await screen.findByRole('radiogroup', { name: 'Asistencia de Castillo, Mateo' })
    await user.click(within(mateo).getByRole('radio', { name: 'Falta' }))
    await user.click(screen.getByRole('button', { name: 'Marcar presente al estudiante restante' }))
    expect(screen.getByText('2 cambios sin guardar')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Guardar asistencia' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(1))
    expect(bodies[0].records).toEqual([
      { student_id: 6, status: 'ABSENT' },
      { student_id: 7, status: 'PRESENT' },
    ])
  })

  it('records course grades and rejects scores out of range', async () => {
    const bodies: { scores: unknown[] }[] = []
    mockApi({
      'GET /me/teaching': () => json(TEACHING),
      'GET /periods': () => json(PERIODS),
      'GET /gradebook': () =>
        json({ classroom_id: 1, subject_id: 2, period_id: 3, rows: STUDENTS.map((s) => ({ ...s, score: null })) }),
      'PUT /gradebook': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ classroom_id: 1, subject_id: 2, period_id: 3, rows: STUDENTS.map((s) => ({ ...s, score: 14.5 })) })
      },
    })
    renderPage(<ClassRegisterPage />, { user: TEACHER_USER, path: '/?hoja=notas' })
    const user = userEvent.setup()

    const mateo = await screen.findByLabelText('Nota de Castillo, Mateo')
    await user.type(mateo, '25')
    expect(screen.getByText('Entre 0 y 20')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar notas' })).toBeDisabled()

    await user.clear(mateo)
    await user.type(mateo, '14,5')
    await user.click(screen.getByRole('button', { name: 'Guardar notas' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(1))
    expect(bodies[0].scores).toEqual([{ student_id: 6, score: 14.5 }])
    expect(await screen.findByText('Guardado.')).toBeInTheDocument()
  })

  it('shows conduct only to tutors', async () => {
    mockApi({
      'GET /me/teaching': () =>
        json({ ...TEACHING, classrooms: [{ ...TEACHING.classrooms[0], is_tutor: false }] }),
      'GET /classrooms/1/attendance': () =>
        json({ classroom_id: 1, date: '2026-10-28', period_id: 3, rows: [] }),
    })
    renderPage(<ClassRegisterPage />, { user: TEACHER_USER })

    expect(await screen.findByRole('tab', { name: 'Notas' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Conducta' })).not.toBeInTheDocument()
  })
})

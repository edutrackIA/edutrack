import { fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DIRECTOR_USER, TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import SchoolSetupPage from './pages/SchoolSetupPage'

const STAFF = [
  { id: 1, full_name: 'Carmen Rojas', email: 'director@edutrack.dev', role: 'DIRECTOR', is_active: true, has_access: true, invitation_sent: null },
  { id: 2, full_name: 'Luis Quispe', email: 'docente@edutrack.dev', role: 'TEACHER', is_active: true, has_access: true, invitation_sent: null },
]

describe('SchoolSetupPage', () => {
  it('adds a period with its dates', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /periods': () => json([]),
      'POST /periods': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ id: 9 }, 201)
      },
    })
    renderPage(<SchoolSetupPage />, { user: DIRECTOR_USER })

    await screen.findByRole('heading', { name: 'Bimestres' })
    await userEvent.setup().selectOptions(screen.getByLabelText('Bimestre'), '2')
    fireEvent.change(screen.getByLabelText('Inicio'), { target: { value: '2026-05-18' } })
    fireEvent.change(screen.getByLabelText('Fin'), { target: { value: '2026-07-17' } })
    await userEvent.setup().click(screen.getByRole('button', { name: 'Agregar bimestre' }))

    await vi.waitFor(() => expect(bodies).toHaveLength(1))
    expect(bodies[0]).toMatchObject({ bimester: 2, start_date: '2026-05-18', end_date: '2026-07-17' })
  })

  it('invites a teacher and shows who still has to accept', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /staff': () => json([...STAFF, { ...STAFF[1], id: 3, full_name: 'Ana Torres', has_access: false }]),
      'POST /staff': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ ...STAFF[1], id: 4, email: 'pedro@colegio.edu.pe', has_access: false, invitation_sent: true }, 201)
      },
    })
    renderPage(<SchoolSetupPage />, { user: DIRECTOR_USER, path: '/?seccion=personal' })
    const user = userEvent.setup()

    const table = await screen.findByRole('table', { name: 'Personal del colegio' })
    expect(within(table).getByText('Invitación pendiente')).toBeInTheDocument()
    expect(within(table).queryByRole('button', { name: /Desactivar a Carmen Rojas/ })).not.toBeInTheDocument()

    await user.type(screen.getByLabelText('Nombre completo'), 'Pedro Salas')
    await user.type(screen.getByLabelText('Correo'), 'pedro@colegio.edu.pe')
    await user.click(screen.getByRole('button', { name: 'Invitar' }))

    expect(await screen.findByText('Invitación enviada a pedro@colegio.edu.pe.')).toBeInTheDocument()
    expect(bodies).toEqual([{ full_name: 'Pedro Salas', email: 'pedro@colegio.edu.pe', role: 'TEACHER' }])
  })

  it('assigns only courses that do not have a teacher yet', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /classrooms': () =>
        json([{ id: 1, year: 2026, grade: 3, section: 'A', tutor: TEACHER_USER, student_count: 10 }]),
      'GET /subjects': () =>
        json([
          { id: 1, name: 'Comunicación' },
          { id: 2, name: 'Matemática' },
        ]),
      'GET /staff': () => json(STAFF),
      'GET /course-assignments': () =>
        json([{ id: 7, classroom_id: 1, classroom: '3° A', subject_id: 2, subject: 'Matemática', teacher_id: 2, teacher: 'Luis Quispe' }]),
      'POST /course-assignments': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ id: 8 }, 201)
      },
    })
    renderPage(<SchoolSetupPage />, { user: DIRECTOR_USER, path: '/?seccion=asignaciones' })
    const user = userEvent.setup()

    expect(await screen.findByRole('list', { name: 'Cursos asignados del aula' })).toHaveTextContent('Matemática')
    const subject = screen.getByLabelText('Curso')
    expect(within(subject).queryByRole('option', { name: 'Matemática' })).not.toBeInTheDocument()

    await user.selectOptions(subject, '1')
    await user.selectOptions(screen.getByLabelText('Docente'), '2')
    await user.click(screen.getByRole('button', { name: 'Asignar' }))

    await vi.waitFor(() => expect(bodies).toEqual([{ classroom_id: 1, subject_id: 1, teacher_id: 2 }]))
  })
})

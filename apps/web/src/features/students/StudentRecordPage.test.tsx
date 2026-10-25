import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DIRECTOR_USER, TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import StudentRecordPage from './pages/StudentRecordPage'

const STUDENT = {
  id: 6,
  code: '20260006',
  first_name: 'Lucía',
  last_name: 'Ramírez Gutiérrez',
  birth_date: '2012-04-10',
  sex: 'F',
  classroom_id: 1,
  guardians: [{ id: 4, email: 'padre@edutrack.dev', full_name: 'Rosa Huamán', role: 'PARENT', institution_id: 1 }],
  latest_risk: null,
}

const RISK = [
  {
    id: 2,
    period_id: 3,
    probability: 0.94,
    level: 'HIGH',
    model_version: 'rf',
    top_factors: [{ feature: 'attendance_rate', label: 'Asistencia', value: 0.78, contribution: 0.3 }],
    created_at: '2026-10-25T00:00:00',
  },
  {
    id: 1,
    period_id: 2,
    probability: 0.45,
    level: 'MEDIUM',
    model_version: 'rf',
    top_factors: [],
    created_at: '2026-07-20T00:00:00',
  },
]

const BASE_HANDLERS = {
  'GET /students/6': () => json(STUDENT),
  'GET /students/6/summary': () =>
    json({ period_id: 3, average_score: 9.8, attendance_rate: 0.78, grades: [] }),
  'GET /students/6/risk': () => json(RISK),
  'GET /students/6/grades': () =>
    json([
      { subject_id: 1, subject: 'Matemática', period_id: 2, score: 12 },
      { subject_id: 1, subject: 'Matemática', period_id: 3, score: 8 },
    ]),
  'GET /students/6/recommendations': () =>
    json([
      {
        id: 9,
        period_id: 3,
        status: 'APPROVED',
        parent_items: ['Asistencia: conversar sobre los motivos de las faltas.'],
        teacher_items: ['Contactar a la familia.'],
        reviewed_at: '2026-10-25T10:00:00',
        sent_at: '2026-10-25T10:00:00',
        created_at: '2026-10-25T00:00:00',
      },
    ]),
  'GET /periods': () =>
    json([
      { id: 2, year: 2026, bimester: 2, start_date: '2026-05-18', end_date: '2026-07-17', label: 'Bimestre 2, 2026' },
      { id: 3, year: 2026, bimester: 3, start_date: '2026-08-03', end_date: '2026-10-02', label: 'Bimestre 3, 2026' },
    ]),
  'GET /classrooms': () =>
    json([{ id: 1, year: 2026, grade: 3, section: 'A', tutor: null, student_count: 10 }]),
}

const FORBIDDEN = () => json({ code: 'FORBIDDEN', message: 'No' }, 403)

describe('StudentRecordPage', () => {
  it('shows the full record to a teacher without family data', async () => {
    mockApi({
      ...BASE_HANDLERS,
      'GET /students/6/commitments': FORBIDDEN,
      'GET /students/6/surveys': FORBIDDEN,
    })

    renderPage(<StudentRecordPage />, {
      user: TEACHER_USER,
      route: '/estudiantes/:studentId',
      path: '/estudiantes/6',
    })

    expect(
      await screen.findByRole('heading', { name: 'Ramírez Gutiérrez, Lucía' }),
    ).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Volver a 3° A' })).toHaveAttribute(
      'href',
      '/aulas?aula=1',
    )
    const history = await screen.findByRole('list', { name: 'Evaluaciones anteriores' })
    expect(await within(history).findByText('Bimestre 2, 2026')).toBeInTheDocument()
    const grades = await screen.findByRole('table', { name: 'Notas por curso y bimestre' })
    expect(within(grades).getByText('(desaprobado)', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('Contactar a la familia.')).toBeInTheDocument()
    expect(
      await screen.findByText('Solo el tutor del aula y la dirección pueden ver las actas.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Encuesta familiar' })).not.toBeInTheDocument()
  })

  it('shows commitments and the family survey to the director', async () => {
    mockApi({
      ...BASE_HANDLERS,
      'GET /students/6/commitments': () =>
        json([
          {
            id: 1,
            meeting_date: '2026-06-12',
            agreements: 'Supervisar una hora diaria de estudio.',
            follow_up_date: '2026-07-10',
            status: 'OPEN',
          },
        ]),
      'GET /students/6/surveys': () =>
        json([
          {
            id: 1,
            period_id: 2,
            study_hours_week: 6,
            parent_education: 'SECONDARY',
            home_internet: true,
            has_study_device: false,
            family_communication: 3,
            student_works: false,
            household_size: 5,
            submitted_at: '2026-06-01T00:00:00',
          },
        ]),
    })

    renderPage(<StudentRecordPage />, {
      user: DIRECTOR_USER,
      route: '/estudiantes/:studentId',
      path: '/estudiantes/6',
    })

    expect(await screen.findByText('Supervisar una hora diaria de estudio.')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Encuesta familiar' })).toBeInTheDocument()
    expect(screen.getByText('6 h por semana')).toBeInTheDocument()
  })

  it('explains when the student cannot be opened', async () => {
    mockApi({
      ...BASE_HANDLERS,
      'GET /students/6': FORBIDDEN,
      'GET /students/6/commitments': FORBIDDEN,
      'GET /students/6/surveys': FORBIDDEN,
    })

    renderPage(<StudentRecordPage />, {
      user: TEACHER_USER,
      route: '/estudiantes/:studentId',
      path: '/estudiantes/6',
    })

    expect(await screen.findByText('No pudimos abrir esta ficha')).toBeInTheDocument()
  })
})

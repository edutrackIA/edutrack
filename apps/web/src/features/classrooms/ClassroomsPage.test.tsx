import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import ClassroomsPage from './pages/ClassroomsPage'

const CLASSROOMS = [
  { id: 1, year: 2026, grade: 3, section: 'A', tutor: TEACHER_USER, student_count: 3 },
  { id: 2, year: 2026, grade: 3, section: 'B', tutor: null, student_count: 1 },
]

const STUDENTS_A = [
  { id: 1, code: '20260001', full_name: 'Salas García, Mateo', classroom: '3° A', risk_level: 'LOW', probability: 0.02 },
  { id: 6, code: '20260006', full_name: 'Ramírez Gutiérrez, Lucía', classroom: '3° A', risk_level: 'HIGH', probability: 0.94 },
  { id: 9, code: '20260009', full_name: 'Paredes Rojas, Adrián', classroom: '3° A', risk_level: null, probability: null },
]

function mockClassrooms() {
  return mockApi({
    'GET /classrooms': () => json(CLASSROOMS),
    'GET /classrooms/1/students': () => json(STUDENTS_A),
    'GET /classrooms/2/students': () => json([]),
  })
}

describe('ClassroomsPage', () => {
  it('lists the teacher classrooms with students sorted by risk', async () => {
    mockClassrooms()

    renderPage(<ClassroomsPage />, { user: TEACHER_USER })

    expect(await screen.findByRole('heading', { name: 'Mis aulas' })).toBeInTheDocument()
    const table = await screen.findByRole('table', {
      name: 'Estudiantes de 3° A con su nivel de riesgo',
    })
    const names = within(table)
      .getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[1].textContent)
    expect(names).toEqual([
      'Ramírez Gutiérrez, Lucía',
      'Salas García, Mateo',
      'Paredes Rojas, Adrián',
    ])
    expect(within(table).getByText('Sin evaluar')).toBeInTheDocument()
    expect(
      within(table).getByRole('link', { name: 'Ver ficha de Ramírez Gutiérrez, Lucía' }),
    ).toHaveAttribute('href', '/estudiantes/6')
  })

  it('filters by risk level through the api', async () => {
    const fetchMock = mockClassrooms()
    renderPage(<ClassroomsPage />, { user: TEACHER_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: 'Alto' }))

    await vi.waitFor(() =>
      expect(fetchMock.mock.calls.map(([url]) => String(url))).toContain(
        '/api/v1/classrooms/1/students?level=HIGH',
      ),
    )
  })

  it('switches to another classroom', async () => {
    mockClassrooms()
    renderPage(<ClassroomsPage />, { user: TEACHER_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: /3° B/ }))

    expect(await screen.findByText('No hay estudiantes con este nivel')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Estudiantes de 3° B' })).toBeInTheDocument()
  })

  it('explains when there are no classrooms', async () => {
    mockApi({ 'GET /classrooms': () => json([]) })

    renderPage(<ClassroomsPage />, { user: TEACHER_USER })

    expect(await screen.findByText('Todavía no tienes aulas asignadas')).toBeInTheDocument()
  })
})

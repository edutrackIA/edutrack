import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import DashboardPage from './pages/DashboardPage'
import type { DashboardSummary } from './types'

const PERIODS = [
  { id: 2, year: 2026, bimester: 2, start_date: '2026-05-18', end_date: '2026-07-17', label: 'Bimestre 2, 2026' },
  { id: 3, year: 2026, bimester: 3, start_date: '2026-08-03', end_date: '2026-10-02', label: 'Bimestre 3, 2026' },
]

const SUMMARY: DashboardSummary = {
  period_id: 3,
  period_label: '2026 · Bimestre 3',
  total_students: 21,
  evaluated_students: 20,
  by_level: { LOW: 17, MEDIUM: 1, HIGH: 2 },
  by_classroom: [
    { classroom_id: 1, label: '3° A', evaluated: 10, low: 7, medium: 1, high: 2 },
    { classroom_id: 2, label: '3° B', evaluated: 10, low: 10, medium: 0, high: 0 },
  ],
  top_factors: [
    { feature: 'attendance_rate', label: 'Asistencia', frequency: 3 },
    { feature: 'avg_score', label: 'Promedio', frequency: 1 },
  ],
}

describe('DashboardPage', () => {
  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', { value: vi.fn(() => 'blob:report'), configurable: true })
    Object.defineProperty(URL, 'revokeObjectURL', { value: vi.fn(), configurable: true })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('summarizes the period in a sentence and per classroom', async () => {
    mockApi({
      'GET /dashboard/summary': () => json(SUMMARY),
      'GET /periods': () => json(PERIODS),
    })

    renderPage(<DashboardPage />)

    expect(
      await screen.findByText('3 de 20 estudiantes necesitan acompañamiento este bimestre.'),
    ).toBeInTheDocument()
    expect(screen.getByText(/1 estudiante aún no tiene evaluación/)).toBeInTheDocument()
    const table = screen.getByRole('table', { name: 'Estudiantes por nivel de riesgo en cada aula' })
    const firstRow = within(table).getAllByRole('row')[1]
    expect(within(firstRow).getByText('3° A')).toBeInTheDocument()
    expect(within(firstRow).getAllByRole('cell').map((cell) => cell.textContent)).toEqual([
      '3° A',
      '',
      '2',
      '1',
      '7',
      '10',
    ])
    expect(screen.getByText('Asistencia')).toBeInTheDocument()
    expect(screen.getByText('3 estudiantes')).toBeInTheDocument()
  })

  it('invites to run an assessment when there is none', async () => {
    mockApi({
      'GET /dashboard/summary': () => json({ ...SUMMARY, period_id: null, period_label: null }),
      'GET /periods': () => json(PERIODS),
    })

    renderPage(<DashboardPage />)

    expect(await screen.findByText('Aún no hay evaluaciones de riesgo')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Descargar reporte PDF' })).not.toBeInTheDocument()
  })

  it('loads another period from the selector', async () => {
    const fetchMock = mockApi({
      'GET /dashboard/summary': () => json(SUMMARY),
      'GET /periods': () => json(PERIODS),
    })
    renderPage(<DashboardPage />)

    await userEvent.setup().selectOptions(await screen.findByLabelText('Bimestre'), '2')

    await vi.waitFor(() =>
      expect(fetchMock.mock.calls.map(([url]) => String(url))).toContain(
        '/api/v1/dashboard/summary?period_id=2',
      ),
    )
  })

  it('downloads the pdf report of the period', async () => {
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    mockApi({
      'GET /dashboard/summary': () => json(SUMMARY),
      'GET /periods': () => json(PERIODS),
      'GET /reports/risk': () =>
        new Response('%PDF-1.4', {
          headers: {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="reporte-riesgo-2026-bimestre-3.pdf"',
          },
        }),
    })
    renderPage(<DashboardPage />)

    await userEvent
      .setup()
      .click(await screen.findByRole('button', { name: 'Descargar reporte PDF' }))

    await vi.waitFor(() => expect(click).toHaveBeenCalledOnce())
    expect(URL.createObjectURL).toHaveBeenCalledOnce()
  })

  it('explains when the summary cannot be loaded', async () => {
    mockApi({
      'GET /dashboard/summary': () => json({ code: 'FORBIDDEN', message: 'No' }, 403),
      'GET /periods': () => json(PERIODS),
    })

    renderPage(<DashboardPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No tienes permiso para realizar esta acción.',
    )
  })
})

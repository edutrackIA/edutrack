import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ANALYST_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import AssessmentsPage from './pages/AssessmentsPage'
import ImportsPage from './pages/ImportsPage'
import ThresholdsPage from './pages/ThresholdsPage'

const PERIODS = [
  { id: 2, year: 2026, bimester: 2, start_date: '2026-05-18', end_date: '2026-07-17', label: 'Bimestre 2, 2026' },
  { id: 3, year: 2026, bimester: 3, start_date: '2026-08-03', end_date: '2026-10-02', label: 'Bimestre 3, 2026' },
]

function importJob(preview: boolean, overrides: Record<string, unknown> = {}) {
  return {
    id: preview ? null : 1,
    kind: 'GRADES',
    filename: 'notas.csv',
    status: 'DONE',
    rows_ok: 2,
    rows_failed: 1,
    errors: [{ row: 3, column: 'subject', message: 'El curso Física no existe' }],
    created_at: preview ? null : '2026-10-29T10:00:00',
    preview,
    ...overrides,
  }
}

describe('ImportsPage', () => {
  it('reviews the file first and imports only after confirming', async () => {
    const sent: Record<string, unknown>[] = []
    mockApi({
      'GET /periods': () => json(PERIODS),
      'POST /imports': (init) => {
        const form = init?.body as FormData
        const preview = form.get('dry_run') === 'true'
        sent.push({
          preview,
          kind: form.get('kind'),
          period: form.get('period_id'),
          file: (form.get('file') as File).name,
        })
        return json(importJob(preview), 202)
      },
    })
    renderPage(<ImportsPage />, { user: ANALYST_USER })
    const user = userEvent.setup()

    await user.click(screen.getByLabelText('Notas'))
    await user.selectOptions(await screen.findByLabelText('Bimestre'), '2')
    await user.upload(
      screen.getByLabelText('Archivo'),
      new File(['student_code,subject,score\n'], 'notas.csv', { type: 'text/csv' }),
    )
    await user.click(screen.getByRole('button', { name: 'Revisar archivo' }))

    expect(await screen.findByText('Todavía no se ha guardado nada.')).toBeInTheDocument()
    expect(screen.getByText(/2 filas listas para importar y 1 con errores/)).toBeInTheDocument()
    expect(
      within(screen.getByRole('table', { name: 'Problemas encontrados en el archivo' })).getByText(
        'El curso Física no existe',
      ),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Importar las 2 filas válidas' }))

    expect(await screen.findByText('2 filas importadas, 1 con errores.')).toBeInTheDocument()
    expect(sent).toEqual([
      { preview: true, kind: 'GRADES', period: '2', file: 'notas.csv' },
      { preview: false, kind: 'GRADES', period: '2', file: 'notas.csv' },
    ])
  })

  it('does not offer to import a file without valid rows', async () => {
    const periods: unknown[] = []
    mockApi({
      'GET /periods': () => json(PERIODS),
      'POST /imports': (init) => {
        periods.push((init?.body as FormData).get('period_id'))
        return json(
          importJob(true, {
            kind: 'STUDENTS',
            status: 'FAILED',
            rows_ok: 0,
            rows_failed: 0,
            errors: [{ row: null, column: null, message: 'El archivo está vacío' }],
          }),
          202,
        )
      },
    })
    renderPage(<ImportsPage />, { user: ANALYST_USER })
    const user = userEvent.setup()

    await user.upload(screen.getByLabelText('Archivo'), new File([''], 'a.csv'))
    await user.click(screen.getByRole('button', { name: 'Revisar archivo' }))

    expect(await screen.findByText(/Ninguna fila se puede importar/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Importar/ })).not.toBeInTheDocument()
    expect(periods).toEqual([null])
  })

  it('cancels the review to fix the file', async () => {
    mockApi({
      'GET /periods': () => json(PERIODS),
      'POST /imports': () => json(importJob(true, { kind: 'STUDENTS' }), 202),
    })
    renderPage(<ImportsPage />, { user: ANALYST_USER })
    const user = userEvent.setup()

    await user.upload(screen.getByLabelText('Archivo'), new File(['x'], 'a.csv'))
    await user.click(screen.getByRole('button', { name: 'Revisar archivo' }))
    await user.click(await screen.findByRole('button', { name: 'Cancelar y corregir el archivo' }))

    expect(screen.getByText('Aquí verás cuántas filas se importaron y qué corregir.')).toBeInTheDocument()
  })
})

describe('AssessmentsPage', () => {
  it('runs the latest period and explains who could not be evaluated', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /periods': () => json(PERIODS),
      'POST /risk-assessments/run': (init) => {
        bodies.push(JSON.parse(String(init?.body)))
        return json({
          evaluated: 18,
          skipped: 1,
          model_version: 'rf-2026.10',
          by_level: { LOW: 15, MEDIUM: 1, HIGH: 2 },
          skipped_students: [
            { student_id: 9, code: '20260009', full_name: 'Paredes, Adrián', reason: 'Sin encuesta familiar' },
          ],
        })
      },
    })
    renderPage(<AssessmentsPage />, { user: ANALYST_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: 'Ejecutar evaluación' }))

    expect(
      await screen.findByRole('heading', { name: 'Bimestre 3, 2026: 18 estudiantes evaluados' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Sin encuesta familiar')).toBeInTheDocument()
    expect(bodies).toEqual([{ period_id: 3 }])
  })

  it('reports when the analysis service is down', async () => {
    mockApi({
      'GET /periods': () => json(PERIODS),
      'POST /risk-assessments/run': () =>
        json({ code: 'ML_SERVICE_UNAVAILABLE', message: 'Down' }, 502),
    })
    renderPage(<AssessmentsPage />, { user: ANALYST_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: 'Ejecutar evaluación' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('El servicio de análisis no está disponible')
  })
})

describe('ThresholdsPage', () => {
  it('validates and saves the thresholds as probabilities', async () => {
    const bodies: unknown[] = []
    mockApi({
      'GET /settings/risk-thresholds': () => json({ medium_from: 0.4, high_from: 0.7 }),
      'PUT /settings/risk-thresholds': (init) => {
        const body = JSON.parse(String(init?.body))
        bodies.push(body)
        return json(body)
      },
    })
    renderPage(<ThresholdsPage />, { user: ANALYST_USER })
    const user = userEvent.setup()

    const medium = await screen.findByLabelText('Moderado desde (%)')
    expect(medium).toHaveValue(40)
    await user.clear(medium)
    await user.type(medium, '80')
    expect(screen.getByRole('alert')).toHaveTextContent('debe ser menor que el alto')
    expect(screen.getByRole('button', { name: 'Guardar umbrales' })).toBeDisabled()

    await user.clear(medium)
    await user.type(medium, '30')
    await user.click(screen.getByRole('button', { name: 'Guardar umbrales' }))

    expect(await screen.findByText('Umbrales guardados.')).toBeInTheDocument()
    await vi.waitFor(() => expect(bodies).toEqual([{ medium_from: 0.3, high_from: 0.7 }]))
  })
})

import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ANALYST_USER, DIRECTOR_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import ModelPerformancePage from './pages/ModelPerformancePage'

const BASE = {
  window_days: 180,
  model_versions: ['rf-2026.10.25-42'],
  min_labeled: 20,
  min_dropouts: 3,
  cases: [
    {
      student_id: 9,
      code: '20260009',
      full_name: 'Paredes, Adrián',
      exit_date: '2026-06-15',
      exit_reason: 'WORK',
      last_level: 'LOW',
      last_probability: 0.12,
      alerted: false,
    },
  ],
}

describe('ModelPerformancePage', () => {
  it('explains the results in plain words when there is enough data', async () => {
    mockApi({
      'GET /model-performance': () =>
        json({
          ...BASE,
          labeled: 20,
          dropouts: 4,
          pending: 0,
          metrics: {
            true_positives: 3,
            false_negatives: 1,
            false_positives: 2,
            true_negatives: 14,
            recall: 0.75,
            precision: 0.6,
          },
        }),
    })

    renderPage(<ModelPerformancePage />, { user: ANALYST_USER })

    expect(await screen.findByText(/estudiantes que se retiraron\./)).toHaveTextContent(
      'El modelo había alertado a 3 de los 4 estudiantes que se retiraron.',
    )
    const cases = screen.getByRole('table', {
      name: 'Estudiantes que se retiraron y la última evaluación previa',
    })
    expect(within(cases).getByText('Trabajo')).toBeInTheDocument()
    expect(within(cases).getByText('No')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descargar datos anonimizados' })).toBeInTheDocument()
  })

  it('shows how far it is from having reliable numbers', async () => {
    mockApi({
      'GET /model-performance': () =>
        json({ ...BASE, labeled: 4, dropouts: 4, pending: 16, metrics: null }),
    })

    renderPage(<ModelPerformancePage />, { user: DIRECTOR_USER })

    expect(await screen.findByText('Aún no hay suficientes resultados reales')).toBeInTheDocument()
    expect(screen.getByText('4 de 20')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Descargar datos anonimizados' })).not.toBeInTheDocument()
  })
})

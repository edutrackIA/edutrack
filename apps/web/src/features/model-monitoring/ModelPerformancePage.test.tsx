import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
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

const MODELS = {
  versions: [
    { version: 'rf-2026.10.25-42', trained_at: '2026-10-25T00:00:00', active: true, synthetic_samples: 4000, school_samples: null, school_dropouts: null, school_holdout: null, trained_by: null, activated_by: null, activated_at: null },
    { version: 'rf-2026.12.01-100000-school', trained_at: '2026-12-01T10:00:00', active: false, synthetic_samples: 4000, school_samples: 210, school_dropouts: 25, school_holdout: { cases: 90, dropouts: 11, recall: 0.82 }, trained_by: 'Jorge Salazar', activated_by: null, activated_at: null },
  ],
  training: { labeled: 300, dropouts: 36, min_labeled: 200, min_dropouts: 20, can_train: true },
}

describe('ModelPerformancePage', () => {
  it('explains the results in plain words when there is enough data', async () => {
    mockApi({
      'GET /models': () => json(MODELS),
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
      'GET /models': () => json(MODELS),
    })

    renderPage(<ModelPerformancePage />, { user: DIRECTOR_USER })

    expect(await screen.findByText('Aún no hay suficientes resultados reales')).toBeInTheDocument()
    expect(screen.getByText('4 de 20')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Descargar datos anonimizados' })).not.toBeInTheDocument()
  })

  it('lets analysis train a candidate and compare it with the active model', async () => {
    mockApi({
      'GET /model-performance': () => json({ ...BASE, labeled: 4, dropouts: 4, pending: 16, metrics: null }),
      'GET /models': () => json(MODELS),
      'POST /models/train': () =>
        json({ candidate: MODELS.versions[1], active_on_holdout: { cases: 90, recall: 0.64 } }),
    })
    renderPage(<ModelPerformancePage />, { user: ANALYST_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: 'Entrenar modelo candidato' }))

    expect(await screen.findByText(/el candidato detecta el 82/)).toHaveTextContent(
      'el modelo actual, el 64',
    )
    expect(screen.queryByRole('button', { name: /^Activar/ })).not.toBeInTheDocument()
  })

  it('lets direction activate a version after confirming', async () => {
    const activated: string[] = []
    mockApi({
      'GET /model-performance': () => json({ ...BASE, labeled: 4, dropouts: 4, pending: 16, metrics: null }),
      'GET /models': () => json(MODELS),
      'POST /models/rf-2026.12.01-100000-school/activation': () => {
        activated.push('school')
        return json({ ...MODELS.versions[1], active: true })
      },
    })
    renderPage(<ModelPerformancePage />, { user: DIRECTOR_USER })
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Activar rf-2026.12.01-100000-school' }))
    await user.click(screen.getByRole('button', { name: 'Sí, activar' }))

    await vi.waitFor(() => expect(activated).toEqual(['school']))
    expect(screen.queryByRole('button', { name: 'Entrenar modelo candidato' })).not.toBeInTheDocument()
  })
})

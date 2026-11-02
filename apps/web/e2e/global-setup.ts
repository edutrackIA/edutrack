import { request } from '@playwright/test'
import { API, PASSWORD, USERS } from './support'

/**
 * Leaves the demo school ready for the tests: risk assessed for the latest period with
 * grades (idempotent; approved recommendations are never regenerated).
 */
export default async function globalSetup(): Promise<void> {
  const api = await request.newContext()
  const login = await api.post(`${API}/auth/login`, {
    data: { email: USERS.analyst, password: PASSWORD },
  })
  if (!login.ok()) {
    throw new Error(
      `Could not sign in as ${USERS.analyst} (${login.status()}). ` +
        'Is the backend running and the demo data loaded (python -m scripts.seed_dev)?',
    )
  }
  const { access_token: token } = (await login.json()) as { access_token: string }
  const headers = { Authorization: `Bearer ${token}` }

  const periods = (await (await api.get(`${API}/periods`, { headers })).json()) as {
    id: number
    has_grades: boolean
  }[]
  const graded = periods.filter((period) => period.has_grades)
  const period = graded[graded.length - 1]
  if (period) {
    const run = await api.post(`${API}/risk-assessments/run`, {
      headers,
      data: { period_id: period.id },
    })
    if (!run.ok()) throw new Error(`Risk assessment failed (${run.status()}): is the ML service up?`)
  }
  await api.dispose()
}

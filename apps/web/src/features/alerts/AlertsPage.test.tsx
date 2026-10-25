import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import AlertsPage from './pages/AlertsPage'

function alert(id: number, name: string, isRead: boolean) {
  return {
    id,
    student: {
      id: id + 10,
      code: `2026000${id}`,
      full_name: name,
      classroom: '3° A',
      risk_level: 'HIGH',
      probability: 0.9,
    },
    level: 'HIGH',
    is_read: isRead,
    created_at: '2026-10-25T00:08:35',
  }
}

describe('AlertsPage', () => {
  it('lists unread alerts and marks one as read', async () => {
    let read = false
    const patches: unknown[] = []
    mockApi({
      'GET /alerts': () =>
        json(
          read
            ? { total: 0, items: [] }
            : { total: 1, items: [alert(1, 'Ramírez Gutiérrez, Lucía', false)] },
        ),
      'PATCH /alerts/1': (init) => {
        patches.push(JSON.parse(String(init?.body)))
        read = true
        return json(alert(1, 'Ramírez Gutiérrez, Lucía', true))
      },
    })
    renderPage(<AlertsPage />, { user: TEACHER_USER })

    const list = await screen.findByRole('list', { name: 'Alertas' })
    expect(within(list).getByText('Ramírez Gutiérrez, Lucía')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sin leer (1)' })).toHaveAttribute('aria-pressed', 'true')

    await userEvent.setup().click(
      within(list).getByRole('button', { name: /Marcar como leída/ }),
    )

    expect(await screen.findByText('No tienes alertas sin leer')).toBeInTheDocument()
    expect(patches).toEqual([{ is_read: true }])
  })

  it('shows all alerts, including the read ones', async () => {
    const fetchMock = mockApi({
      'GET /alerts': () =>
        json({
          total: 2,
          items: [alert(1, 'Ramírez Gutiérrez, Lucía', false), alert(2, 'Córdova, Daniela', true)],
        }),
    })
    renderPage(<AlertsPage />, { user: TEACHER_USER })

    await userEvent.setup().click(await screen.findByRole('button', { name: 'Todas' }))

    expect(await screen.findByText('Leída')).toBeInTheDocument()
    expect(fetchMock.mock.calls.map(([url]) => String(url))).toContain('/api/v1/alerts?size=100')
  })
})

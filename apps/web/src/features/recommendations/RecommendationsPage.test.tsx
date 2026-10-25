import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { TEACHER_USER } from '../../test/fixtures'
import { renderPage } from '../../test/render'
import { json, mockApi } from '../../test/server'
import RecommendationsPage from './pages/RecommendationsPage'

function recommendation(id: number, name: string, status = 'PENDING_REVIEW', sentAt: string | null = null) {
  return {
    id,
    student: { id: id + 10, code: `2026000${id}`, full_name: name, classroom: '3° A', risk_level: 'HIGH', probability: 0.9 },
    period_id: 3,
    status,
    parent_items: ['Asistencia: conversen sobre las faltas.', 'Seguimiento: el tutor estará atento.'],
    teacher_items: ['Contactar a la familia.'],
    reviewed_at: null,
    sent_at: sentAt,
    created_at: '2026-10-25T00:08:35',
    family_contacts: 1,
  }
}

describe('RecommendationsPage', () => {
  it('edits the family text and approves, which saves and then sends', async () => {
    const calls: string[] = []
    let patched: unknown = null
    mockApi({
      'GET /recommendations': () => json(calls.includes('approve') ? [] : [recommendation(1, 'Ramírez Gutiérrez, Lucía')]),
      'PATCH /recommendations/1': (init) => {
        calls.push('patch')
        patched = JSON.parse(String(init?.body))
        return json(recommendation(1, 'Ramírez Gutiérrez, Lucía'))
      },
      'POST /recommendations/1/approve': () => {
        calls.push('approve')
        return json(recommendation(1, 'Ramírez Gutiérrez, Lucía', 'APPROVED', '2026-10-25T10:00:00'))
      },
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER })
    const user = userEvent.setup()

    const first = await screen.findByLabelText('Recomendación 1')
    await user.clear(first)
    await user.type(first, 'Asistencia: revisen juntos el horario de la semana.')
    await user.click(screen.getByRole('button', { name: 'Quitar la recomendación 2' }))
    await user.click(screen.getByRole('button', { name: 'Aprobar y enviar a la familia' }))

    expect(
      await screen.findByText('Recomendación de Ramírez Gutiérrez, Lucía aprobada y enviada a la familia.'),
    ).toBeInTheDocument()
    expect(calls).toEqual(['patch', 'approve'])
    expect(patched).toEqual({ parent_items: ['Asistencia: revisen juntos el horario de la semana.'] })
  })

  it('approves without editing in a single request', async () => {
    const calls: string[] = []
    mockApi({
      'GET /recommendations': () => json([recommendation(1, 'Ramírez Gutiérrez, Lucía')]),
      'POST /recommendations/1/approve': () => {
        calls.push('approve')
        return json(recommendation(1, 'Ramírez Gutiérrez, Lucía', 'APPROVED', null))
      },
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER })

    await userEvent.setup().click(
      await screen.findByRole('button', { name: 'Aprobar y enviar a la familia' }),
    )

    expect(await screen.findByText(/el correo no se pudo enviar/)).toBeInTheDocument()
    expect(calls).toEqual(['approve'])
  })

  it('warns when the student has no guardian with an email', async () => {
    const noContact = { ...recommendation(1, 'Ramírez Gutiérrez, Lucía'), family_contacts: 0 }
    mockApi({
      'GET /recommendations': () => json([noContact]),
      'POST /recommendations/1/approve': () =>
        json({ ...noContact, status: 'APPROVED', sent_at: null }),
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER })

    expect(
      await screen.findByText(/no tiene un apoderado con correo registrado\. Puedes aprobar/),
    ).toBeInTheDocument()
    await userEvent
      .setup()
      .click(screen.getByRole('button', { name: 'Aprobar y enviar a la familia' }))

    expect(await screen.findByText(/no se envió ningún correo/)).toBeInTheDocument()
  })

  it('asks for confirmation before discarding', async () => {
    const calls: string[] = []
    mockApi({
      'GET /recommendations': () => json([recommendation(1, 'Ramírez Gutiérrez, Lucía')]),
      'POST /recommendations/1/discard': () => {
        calls.push('discard')
        return json(recommendation(1, 'Ramírez Gutiérrez, Lucía', 'DISCARDED'))
      },
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER })
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Descartar' }))
    expect(calls).toEqual([])
    await user.click(screen.getByRole('button', { name: 'Sí, descartar' }))

    expect(await screen.findByText('Recomendación de Ramírez Gutiérrez, Lucía descartada.')).toBeInTheDocument()
    expect(calls).toEqual(['discard'])
  })

  it('lets the tutor resend an approved recommendation whose email failed', async () => {
    const calls: string[] = []
    mockApi({
      'GET /recommendations': () => json([recommendation(1, 'Ramírez Gutiérrez, Lucía', 'APPROVED', null)]),
      'POST /recommendations/1/send': () => {
        calls.push('send')
        return json(recommendation(1, 'Ramírez Gutiérrez, Lucía', 'APPROVED', '2026-10-25T10:00:00'))
      },
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER, path: '/?estado=APPROVED' })
    const user = userEvent.setup()

    const editor = await screen.findByRole('article', { name: 'Ramírez Gutiérrez, Lucía' })
    await user.click(within(editor).getByRole('button', { name: 'Reenviar correo' }))

    expect(await screen.findByText('Correo enviado a la familia.')).toBeInTheDocument()
    expect(calls).toEqual(['send'])
  })

  it('orders the queue by risk priority and then alphabetically', async () => {
    const at = (id: number, name: string, level: string) => {
      const item = recommendation(id, name)
      return { ...item, student: { ...item.student, risk_level: level } }
    }
    mockApi({
      'GET /recommendations': () =>
        json([
          at(1, 'Salas García, Ana', 'LOW'),
          at(2, 'Vargas, Zoe', 'HIGH'),
          at(3, 'Castillo, Beto', 'MEDIUM'),
          at(4, 'Alarcón, Abel', 'HIGH'),
        ]),
    })
    renderPage(<RecommendationsPage />, { user: TEACHER_USER })

    const queue = await screen.findByRole('navigation', { name: 'Por revisar' })
    const names = within(queue)
      .getAllByRole('button')
      .map((button) => button.querySelector('span')?.textContent)

    expect(names).toEqual(['Alarcón, Abel', 'Vargas, Zoe', 'Castillo, Beto', 'Salas García, Ana'])
  })

  it('explains an empty queue', async () => {
    mockApi({ 'GET /recommendations': () => json([]) })

    renderPage(<RecommendationsPage />, { user: TEACHER_USER })

    expect(await screen.findByText('No tienes recomendaciones por revisar')).toBeInTheDocument()
  })
})

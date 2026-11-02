import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RiskBadge } from './RiskBadge'

describe('RiskBadge', () => {
  it.each([
    ['LOW', 'Bajo'],
    ['MEDIUM', 'Moderado'],
    ['HIGH', 'Alto'],
  ] as const)('shows the %s level as text, not only color', (level, label) => {
    render(<RiskBadge level={level} />)

    expect(screen.getByText(label)).toBeInTheDocument()
  })
})

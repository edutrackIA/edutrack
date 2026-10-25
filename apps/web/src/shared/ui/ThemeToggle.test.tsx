import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { ThemeToggle } from './ThemeToggle'

describe('ThemeToggle', () => {
  afterEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('follows the system by default', () => {
    render(<ThemeToggle />)

    expect(screen.getByRole('button', { name: 'Sistema' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('switches to dark and remembers the choice', async () => {
    render(<ThemeToggle />)

    await userEvent.setup().click(screen.getByRole('button', { name: 'Oscuro' }))

    expect(document.documentElement).toHaveClass('dark')
    expect(localStorage.getItem('edutrack.theme')).toBe('dark')
  })

  it('returns to light', async () => {
    localStorage.setItem('edutrack.theme', 'dark')
    document.documentElement.classList.add('dark')
    render(<ThemeToggle />)

    await userEvent.setup().click(screen.getByRole('button', { name: 'Claro' }))

    expect(document.documentElement).not.toHaveClass('dark')
  })
})

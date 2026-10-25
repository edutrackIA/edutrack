import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { clearTokens } from './shared/api/tokens'

afterEach(() => {
  cleanup()
  clearTokens()
  vi.unstubAllGlobals()
})

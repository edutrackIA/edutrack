import { QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { createQueryClient } from '../app/query-client'
import { routes } from '../app/routes'
import { AuthProvider } from '../features/auth/AuthProvider'

export function renderApp(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const queryClient = createQueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>,
  )
  return router
}

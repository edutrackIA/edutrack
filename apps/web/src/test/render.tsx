import { QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactNode } from 'react'
import { createMemoryRouter, MemoryRouter, Route, RouterProvider, Routes } from 'react-router-dom'
import { createQueryClient } from '../app/query-client'
import { routes } from '../app/routes'
import { AuthContext } from '../features/auth/auth-context'
import { AuthProvider } from '../features/auth/AuthProvider'
import type { User } from '../features/auth/types'

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

function toEntry(path: string, state: unknown) {
  const [pathname, search] = path.split('?')
  return { pathname, search: search ? `?${search}` : '', state }
}

interface RenderPageOptions {
  /** Signed-in user seen by the page. */
  user?: User
  /** Route pattern with params, e.g. "/estudiantes/:studentId". */
  route?: string
  /** Initial URL, e.g. "/estudiantes/6?tab=notas". */
  path?: string
  /** Router state of the initial URL, as a Link with `state` would set it. */
  state?: unknown
}

/** Renders a single page with data fetching and routing, without the login flow. */
export function renderPage(
  page: ReactNode,
  { user, route, path = '/', state }: RenderPageOptions = {},
) {
  const queryClient = createQueryClient()
  queryClient.setDefaultOptions({ queries: { retry: false } })
  const auth = {
    status: user ? ('authenticated' as const) : ('anonymous' as const),
    user: user ?? null,
    sessionExpired: false,
    login: async () => {
      throw new Error('login is not available in page tests')
    },
    logout: async () => {},
  }
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={[toEntry(path, state)]}>
          {route ? (
            <Routes>
              <Route path={route} element={page} />
            </Routes>
          ) : (
            page
          )}
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

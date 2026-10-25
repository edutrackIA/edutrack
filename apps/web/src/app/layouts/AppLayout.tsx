import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../features/auth/auth-context'
import { ROLE_LABELS } from '../../features/auth/roles'
import { Button } from '../../shared/ui/Button'
import { ThemeToggle } from '../../shared/ui/ThemeToggle'
import { NAV_ITEMS } from '../navigation'

export function AppLayout() {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2"
      >
        Saltar al contenido
      </a>

      <aside className="border-b border-rule bg-surface lg:border-b-0 lg:border-r">
        <div className="px-6 pb-2 pt-5 lg:pb-6 lg:pt-8">
          <Link to="/" className="font-figure text-2xl font-semibold text-ink">
            EduTrack
          </Link>
        </div>
        <nav aria-label="Principal" className="overflow-x-auto px-3 pb-3">
          <ul className="flex gap-1 lg:flex-col">
            {NAV_ITEMS[user.role].map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `block whitespace-nowrap rounded-md px-3 py-2 ${
                      isActive
                        ? 'bg-accent-tint font-bold text-accent-strong'
                        : 'text-ink-soft hover:bg-paper hover:text-ink'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="flex flex-wrap items-center justify-end gap-4 border-b border-rule bg-surface px-6 py-3">
          <ThemeToggle />
          <div className="text-right">
            <p className="font-bold text-ink">{user.full_name}</p>
            <p className="text-sm text-ink-soft">{ROLE_LABELS[user.role]}</p>
          </div>
          <Button variant="secondary" onClick={() => void logout()}>
            Cerrar sesión
          </Button>
        </header>
        <main id="contenido" className="mx-auto w-full max-w-6xl flex-1 px-6 py-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

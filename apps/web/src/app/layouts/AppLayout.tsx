import { Link, NavLink, Outlet } from 'react-router-dom'
import { useUnreadAlertsCount } from '../../features/alerts/api'
import { useAuth } from '../../features/auth/auth-context'
import { ConsentGate } from '../../features/privacy/components/ConsentGate'
import { ROLE_LABELS } from '../../features/auth/roles'
import { Button } from '../../shared/ui/Button'
import { ThemeToggle } from '../../shared/ui/ThemeToggle'
import { NAV_ITEMS } from '../navigation'

export function AppLayout() {
  const { user, logout } = useAuth()
  const unreadAlerts = useUnreadAlertsCount(user?.role === 'TEACHER')
  if (!user) return null

  return (
    <div className="min-h-screen lg:grid lg:h-screen lg:grid-cols-[15rem_1fr] lg:overflow-hidden">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2"
      >
        Saltar al contenido
      </a>

      <aside className="border-b border-rule bg-surface lg:overflow-y-auto lg:border-b-0 lg:border-r">
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
                  {item.to === '/alertas' && !!unreadAlerts.data && (
                    <span className="ml-2 rounded-full bg-risk-high-mark px-2 py-0.5 text-xs font-bold text-white">
                      {unreadAlerts.data}
                      <span className="sr-only"> sin leer</span>
                    </span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-col lg:min-h-0">
        <header className="flex shrink-0 flex-wrap items-center justify-end gap-4 border-b border-rule bg-surface px-6 py-3">
          <ThemeToggle />
          <Link to="/mi-cuenta" className="rounded-md px-2 py-1 text-right hover:bg-paper">
            <span className="block font-bold text-ink">{user.full_name}</span>
            <span className="block text-sm text-ink-soft">{ROLE_LABELS[user.role]}</span>
            <span className="sr-only"> (mi cuenta)</span>
          </Link>
          <Button variant="secondary" onClick={() => void logout()}>
            Cerrar sesión
          </Button>
        </header>
        {/* Pages scroll inside this area, never the whole window. */}
        <div className="flex-1 lg:min-h-0 lg:overflow-y-auto">
          <main id="contenido" className="mx-auto w-full max-w-7xl px-6 py-6 lg:h-full lg:px-10">
            <ConsentGate>
              <Outlet />
            </ConsentGate>
          </main>
        </div>
      </div>
    </div>
  )
}

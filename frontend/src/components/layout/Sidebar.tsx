import { NavLink } from 'react-router-dom'

type SidebarProps = {
  isOpen: boolean
  onClose: () => void
}

type NavigationItem = {
  label: string
  to: string
  icon: 'dashboard' | 'analysis' | 'datasets'
}

const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    to: '/dashboard',
    icon: 'dashboard',
  },
  {
    label: 'New Analysis',
    to: '/new-analysis',
    icon: 'analysis',
  },
  {
    label: 'Datasets',
    to: '/datasets',
    icon: 'datasets',
  },
]

function NavigationIcon({ icon }: { icon: NavigationItem['icon'] }) {
  if (icon === 'dashboard') {
    return (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        aria-hidden="true"
      >
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    )
  }

  if (icon === 'analysis') {
    return (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 3v18M3 12h18"
        />
        <circle cx="12" cy="12" r="8.5" />
      </svg>
    )
  }

  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      aria-hidden="true"
    >
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
      <path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
    </svg>
  )
}

function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800 bg-slate-950 transition-transform duration-300 lg:static lg:z-auto lg:w-64 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-20 items-center border-b border-slate-800 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500 font-bold text-slate-950 shadow-lg shadow-emerald-500/10">
              W
            </div>

            <div>
              <p className="font-bold tracking-tight text-white">
                Watershed
              </p>

              <p className="text-xs text-slate-500">
                Impact Analysis
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-6">
          <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
            Workspace
          </p>

          <nav className="space-y-1">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  [
                    'group flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition',
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-300'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100',
                  ].join(' ')
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={
                        isActive
                          ? 'text-emerald-400'
                          : 'text-slate-500 transition group-hover:text-slate-300'
                      }
                    >
                      <NavigationIcon icon={item.icon} />
                    </span>

                    <span>{item.label}</span>

                    {isActive && (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="border-t border-slate-800 p-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              <p className="text-xs font-semibold text-slate-300">
                Web GIS Workspace
              </p>
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Geospatial watershed impact analysis interface.
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
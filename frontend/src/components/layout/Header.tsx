import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'

type HeaderProps = {
  onMenuClick: () => void
}

function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  // Get user initials (up to 2 uppercase letters)
  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : 'WA'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/90 px-4 backdrop-blur sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 text-slate-300 transition hover:border-slate-700 hover:bg-slate-800 hover:text-white lg:hidden"
          aria-label="Open navigation"
        >
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
              d="M4 7h16M4 12h16M4 17h16"
            />
          </svg>
        </button>

        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
            Watershed Intelligence
          </p>

          <p className="text-sm font-semibold text-slate-200">
            Geospatial Analysis Workspace
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 sm:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-emerald-300">
            Authenticated
          </span>
        </div>

        {/* User profile badge */}
        <div className="flex items-center gap-2.5 rounded-xl border border-slate-800 bg-slate-900/90 py-1 px-2.5">
          <div
            data-testid="user-avatar"
            className="flex h-8 w-8 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-950/60 text-xs font-bold text-emerald-300"
          >
            {initials}
          </div>
          <span
            data-testid="user-display-name"
            className="hidden text-xs font-medium text-slate-300 sm:inline-block max-w-[120px] truncate"
          >
            {user?.username || 'User'}
          </span>

          <button
            type="button"
            data-testid="logout-button"
            onClick={handleLogout}
            title="Log out of session"
            aria-label="Log out"
            className="ml-1 flex items-center gap-1.5 rounded-lg border border-slate-700/60 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:border-rose-500/40 hover:bg-rose-950/30 hover:text-rose-200"
          >
            <svg
              className="h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75"
              />
            </svg>
            <span className="hidden sm:inline">Log Out</span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header

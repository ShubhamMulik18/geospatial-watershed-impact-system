import { Link } from 'react-router-dom'

function QuickActions() {
  return (
    <section
      aria-labelledby="quick-actions-title"
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Workspace
        </p>

        <h2
          id="quick-actions-title"
          className="mt-2 text-lg font-semibold text-white"
        >
          Quick Actions
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          Start a watershed assessment or explore the datasets available to the
          analysis workflow.
        </p>
      </div>

      <div className="mt-6 space-y-3">
        <Link
          to="/new-analysis"
          className="group flex items-center justify-between rounded-xl bg-emerald-500 px-4 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
        >
          <span className="flex items-center gap-3">
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                d="M12 5v14M5 12h14"
              />
            </svg>

            Start New Analysis
          </span>

          <svg
            viewBox="0 0 24 24"
            className="h-4 w-4 transition-transform group-hover:translate-x-1"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m9 18 6-6-6-6"
            />
          </svg>
        </Link>

        <Link
          to="/datasets"
          className="group flex items-center justify-between rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-3.5 text-sm font-semibold text-slate-200 transition hover:border-slate-600 hover:bg-slate-800"
        >
          <span className="flex items-center gap-3">
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5 text-slate-400"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              aria-hidden="true"
            >
              <ellipse cx="12" cy="5" rx="8" ry="3" />
              <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
              <path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
            </svg>

            Browse Datasets
          </span>

          <svg
            viewBox="0 0 24 24"
            className="h-4 w-4 text-slate-500 transition-transform group-hover:translate-x-1"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m9 18 6-6-6-6"
            />
          </svg>
        </Link>
      </div>

      <div className="mt-6 border-t border-slate-800 pt-5">
        <p className="text-xs leading-5 text-slate-500">
          Analysis execution and dataset processing will connect to backend
          services during the integration phases.
        </p>
      </div>
    </section>
  )
}

export default QuickActions
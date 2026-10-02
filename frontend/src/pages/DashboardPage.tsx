import { Link } from 'react-router-dom'

import DashboardSummary from '../components/dashboard/DashboardSummary'
import QuickActions from '../components/dashboard/QuickActions'
import RecentAnalyses from '../components/dashboard/RecentAnalyses'

function DashboardPage() {
  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Overview
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Watershed Dashboard
          </h1>

          <p className="mt-3 max-w-2xl leading-7 text-slate-400">
            Monitor watershed analyses, review recent activity, and access the
            tools required for geospatial impact assessment.
          </p>
        </div>

        <Link
          to="/new-analysis"
          className="inline-flex w-fit items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/10 transition hover:bg-emerald-400"
        >
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

          New Analysis
        </Link>
      </section>

      <DashboardSummary />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <RecentAnalyses />

        <QuickActions />
      </div>

      <section className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 px-6 py-5">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-400">
            <svg
              viewBox="0 0 24 24"
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="9" />
              <path
                strokeLinecap="round"
                d="M12 11v5M12 8h.01"
              />
            </svg>
          </div>

          <div>
            <p className="text-sm font-medium text-slate-300">
              Development data
            </p>

            <p className="mt-1 text-sm leading-6 text-slate-500">
              Dashboard statistics and recent analysis records currently use
              clearly identified demo data. Real values will replace them when
              frontend API integration is implemented.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default DashboardPage
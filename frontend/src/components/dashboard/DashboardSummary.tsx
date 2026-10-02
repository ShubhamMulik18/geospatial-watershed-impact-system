type SummaryCard = {
  label: string
  value: string
  description: string
  icon: 'total' | 'completed' | 'processing' | 'datasets'
}

const summaryCards: SummaryCard[] = [
  {
    label: 'Total Analyses',
    value: '12',
    description: 'Demo analysis records',
    icon: 'total',
  },
  {
    label: 'Completed',
    value: '8',
    description: 'Demo completed analyses',
    icon: 'completed',
  },
  {
    label: 'Processing',
    value: '2',
    description: 'Demo active analyses',
    icon: 'processing',
  },
  {
    label: 'Datasets',
    value: '6',
    description: 'Demo available datasets',
    icon: 'datasets',
  },
]

function SummaryIcon({ icon }: { icon: SummaryCard['icon'] }) {
  if (icon === 'total') {
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
          d="M4 19V9m5 10V5m5 14v-7m5 7V3"
        />
      </svg>
    )
  }

  if (icon === 'completed') {
    return (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="9" />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="m8 12 2.5 2.5L16 9"
        />
      </svg>
    )
  }

  if (icon === 'processing') {
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
          d="M12 3a9 9 0 1 1-6.36 2.64"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M5.64 3.64v4h4"
        />
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

function DashboardSummary() {
  return (
    <section aria-labelledby="dashboard-summary-title">
      <div className="mb-4 flex items-center justify-between">
        <h2
          id="dashboard-summary-title"
          className="text-sm font-semibold text-slate-300"
        >
          Analysis Overview
        </h2>

        <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-300">
          Demo data
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((card) => (
          <article
            key={card.label}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-400">
                  {card.label}
                </p>

                <p className="mt-3 text-3xl font-bold tracking-tight text-white">
                  {card.value}
                </p>
              </div>

              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-400">
                <SummaryIcon icon={card.icon} />
              </div>
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500">
              {card.description}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default DashboardSummary
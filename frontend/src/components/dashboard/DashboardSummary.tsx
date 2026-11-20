type DashboardSummaryProps = {
  total?: number
  completed?: number
  processing?: number
  datasets?: number
  isLoading?: boolean
}

type SummaryCard = {
  label: string
  value: number
  description: string
  icon: 'total' | 'completed' | 'processing' | 'datasets'
}

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
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 7v10c0 2 3.5 3 8 3s8-1 8-3V7"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 7c0-2 3.5-3 8-3s8 1 8 3"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 12c0 2 3.5 3 8 3s8-1 8-3"
      />
    </svg>
  )
}

function DashboardSummary({
  total = 0,
  completed = 0,
  processing = 0,
  datasets = 0,
  isLoading = false,
}: DashboardSummaryProps) {
  const cards: SummaryCard[] = [
    {
      label: 'Total Analyses',
      value: total,
      description: 'Persisted analysis records',
      icon: 'total',
    },
    {
      label: 'Completed',
      value: completed,
      description: 'Successfully evaluated',
      icon: 'completed',
    },
    {
      label: 'Processing',
      value: processing,
      description: 'Active analyses',
      icon: 'processing',
    },
    {
      label: 'Datasets',
      value: datasets,
      description: 'Catalogue satellite datasets',
      icon: 'datasets',
    },
  ]

  return (
    <section
      aria-labelledby="dashboard-summary-title"
      className="space-y-4"
    >
      <h2
        id="dashboard-summary-title"
        className="sr-only"
      >
        Analysis Summary Statistics
      </h2>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article
            key={card.label}
            className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                {card.label}
              </p>

              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-800 bg-slate-950 text-emerald-400">
                <SummaryIcon icon={card.icon} />
              </div>
            </div>

            <div className="mt-4">
              {isLoading ? (
                <div className="h-9 w-16 animate-pulse rounded bg-slate-800" />
              ) : (
                <p className="text-3xl font-bold tracking-tight text-white">
                  {card.value}
                </p>
              )}

              <p className="mt-1 text-xs text-slate-400">
                {card.description}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

export default DashboardSummary

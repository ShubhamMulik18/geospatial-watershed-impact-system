export type ProcessingState =
  | 'idle'
  | 'created'
  | 'validating'
  | 'processing'
  | 'completed'
  | 'failed'

type ProcessingStatusProps = {
  status: ProcessingState
  message?: string | null
}

const statusDetails: Record<
  ProcessingState,
  {
    label: string
    description: string
  }
> = {
  idle: {
    label: 'Not Started',
    description:
      'Configure the analysis before starting processing.',
  },
  created: {
    label: 'Created',
    description:
      'The analysis request has been created.',
  },
  validating: {
    label: 'Validating',
    description:
      'The analysis configuration is being validated.',
  },
  processing: {
    label: 'Processing',
    description:
      'The watershed analysis is currently processing.',
  },
  completed: {
    label: 'Completed',
    description:
      'The analysis completed successfully.',
  },
  failed: {
    label: 'Failed',
    description:
      'The analysis could not be completed.',
  },
}

function ProcessingStatus({
  status,
  message,
}: ProcessingStatusProps) {
  const details = statusDetails[status]

  const isActive =
    status === 'created' ||
    status === 'validating' ||
    status === 'processing'

  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Analysis Status
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Processing Status
        </h2>
      </div>

      <div className="p-6">
        <div className="flex items-start gap-4">
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${
              isFailed
                ? 'bg-red-500/10 text-red-300'
                : isCompleted
                  ? 'bg-emerald-500/10 text-emerald-300'
                  : isActive
                    ? 'bg-amber-500/10 text-amber-300'
                    : 'bg-slate-800 text-slate-400'
            }`}
          >
            {isActive ? (
              <span className="h-4 w-4 animate-pulse rounded-full bg-current" />
            ) : (
              <span className="h-3 w-3 rounded-full bg-current" />
            )}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="font-semibold text-slate-200">
                {details.label}
              </p>

              <span
                className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                  isFailed
                    ? 'border-red-500/30 bg-red-500/10 text-red-300'
                    : isCompleted
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                      : isActive
                        ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                        : 'border-slate-700 text-slate-400'
                }`}
              >
                {status}
              </span>
            </div>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              {message ?? details.description}
            </p>
          </div>
        </div>

        {isActive && (
          <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
            <p className="text-xs leading-5 text-amber-200/80">
              Processing progress is status-based. No estimated
              percentage is shown unless the backend provides one.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}

export default ProcessingStatus
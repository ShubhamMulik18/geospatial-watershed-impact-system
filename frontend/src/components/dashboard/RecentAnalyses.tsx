import { Link } from 'react-router-dom'
import type { AnalysisResponse } from '../../services/analysisApi'

type RecentAnalysesProps = {
  analyses?: AnalysisResponse[]
  isLoading?: boolean
  error?: string | null
  onRetry?: () => void
}

function getStatusBadge(status: string) {
  const norm = status.toLowerCase()
  if (norm === 'completed') {
    return {
      label: 'Completed',
      style: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
    }
  }
  if (norm === 'failed') {
    return {
      label: 'Failed',
      style: 'border-rose-500/20 bg-rose-500/10 text-rose-400',
    }
  }
  return {
    label: 'Processing',
    style: 'border-amber-500/20 bg-amber-500/10 text-amber-400',
  }
}

function RecentAnalyses({
  analyses = [],
  isLoading = false,
  error = null,
  onRetry,
}: RecentAnalysesProps) {
  return (
    <section
      aria-labelledby="recent-analyses-title"
      className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70"
    >
      <div className="flex flex-col gap-3 border-b border-slate-800 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2
              id="recent-analyses-title"
              className="text-lg font-semibold text-white"
            >
              Recent Analyses
            </h2>

            <span
              className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                isLoading
                  ? 'border-slate-700 bg-slate-800 text-slate-400'
                  : error
                    ? 'border-rose-500/20 bg-rose-500/10 text-rose-400'
                    : analyses.length > 0
                      ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
                      : 'border-slate-800 bg-slate-950 text-slate-500'
              }`}
            >
              {isLoading
                ? 'Loading records...'
                : error
                  ? 'Connection Error'
                  : `${analyses.length} Records`}
            </span>
          </div>

          <p className="mt-1 text-sm text-slate-400">
            Chronological log of watershed assessments evaluated on this system.
          </p>
        </div>

        <Link
          to="/new-analysis"
          className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-emerald-500/50 hover:text-white"
        >
          <span>Run New Assessment</span>
          <svg
            className="h-3.5 w-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </Link>
      </div>

      <div className="p-6">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex animate-pulse items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/40 p-4"
              >
                <div className="space-y-2">
                  <div className="h-4 w-48 rounded bg-slate-800" />
                  <div className="h-3 w-32 rounded bg-slate-800/60" />
                </div>
                <div className="h-6 w-20 rounded bg-slate-800" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center">
            <svg
              className="mx-auto h-8 w-8 text-rose-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-semibold text-white">
              Failed to load recent analyses
            </h3>
            <p className="mt-1 text-xs text-rose-300/80">{error}</p>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="mt-4 rounded-lg bg-rose-500/20 px-3.5 py-1.5 text-xs font-semibold text-rose-300 transition hover:bg-rose-500/30"
              >
                Retry
              </button>
            )}
          </div>
        ) : analyses.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-8 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900 text-slate-500">
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="mt-3 text-base font-semibold text-white">
              No analyses recorded yet
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              Upload a field photograph and configure satellite observations to perform your first watershed impact evaluation.
            </p>
            <div className="mt-5">
              <Link
                to="/new-analysis"
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-slate-950 shadow transition hover:bg-emerald-400"
              >
                Start New Analysis
              </Link>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80 overflow-hidden rounded-xl border border-slate-800 bg-slate-950/40">
            {analyses.map((analysis) => {
              const statusInfo = getStatusBadge(analysis.status)
              const structureName = analysis.prediction?.class || 'Watershed Assessment'
              const numObservations = analysis.inputs?.dataset_ids?.length || 2
              const indicators = (analysis.inputs?.indicators || ['ndvi'])
                .map((i) => i.toUpperCase())
                .join(', ')

              return (
                <div
                  key={analysis.analysis_id}
                  className="flex flex-col justify-between gap-4 p-4 transition hover:bg-slate-900/50 sm:flex-row sm:items-center"
                >
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="font-semibold text-white">
                        {structureName}
                      </span>
                      <span
                        className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${statusInfo.style}`}
                      >
                        {statusInfo.label}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span>ID: <code className="font-mono text-slate-300">{analysis.analysis_id.slice(0, 8)}...</code></span>
                      <span>•</span>
                      <span>{numObservations} Observations</span>
                      <span>•</span>
                      <span>Indicators: {indicators}</span>
                    </div>
                  </div>

                  <Link
                    to={`/analyses/${analysis.analysis_id}`}
                    className="inline-flex items-center gap-1.5 self-start text-xs font-semibold text-emerald-400 transition hover:text-emerald-300 sm:self-center"
                  >
                    <span>View Results</span>
                    <svg
                      className="h-3.5 w-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </Link>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export default RecentAnalyses

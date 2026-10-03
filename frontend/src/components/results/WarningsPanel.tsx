import type { ResultQuality } from '../../types/analysisResult'

type WarningsPanelProps = {
  warnings: string[]
  quality: ResultQuality
}

function WarningsPanel({
  warnings,
  quality,
}: WarningsPanelProps) {
  const hasWarnings = warnings.length > 0

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-400">
          Quality & Warnings
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Result Reliability Information
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Review quality information and warnings associated with the
          completed analysis.
        </p>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Quality Status
          </p>

          <p className="mt-2 font-semibold text-slate-200">
            {quality.status ?? 'Unavailable'}
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            {quality.summary ?? 'Quality information is unavailable.'}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Analysis Warnings
          </p>

          {hasWarnings ? (
            <ul className="mt-3 space-y-3">
              {warnings.map((warning, index) => (
                <li
                  key={`${warning}-${index}`}
                  className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm leading-6 text-amber-200"
                >
                  {warning}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm leading-6 text-slate-500">
              No warnings were returned for this analysis.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}

export default WarningsPanel
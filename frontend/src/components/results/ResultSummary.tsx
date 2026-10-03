import MetricCard from './MetricCard'

type ResultSummaryProps = {
  predictedClass: string | null
  confidence: number | null
  datasetCount: number
  indicatorCount: number
}

function ResultSummary({
  predictedClass,
  confidence,
  datasetCount,
  indicatorCount,
}: ResultSummaryProps) {
  return (
    <section className="space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Result Summary
        </p>

        <h2 className="mt-1 text-2xl font-semibold text-white">
          Analysis Overview
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Summary information returned for the completed watershed
          analysis.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Predicted Structure
          </p>

          <p className="mt-3 text-2xl font-bold text-white">
            {predictedClass ?? 'Unavailable'}
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Structure classification associated with this analysis.
          </p>
        </article>

        <MetricCard
          label="Confidence"
          value={
            confidence !== null
              ? confidence * 100
              : null
          }
          unit="%"
          description="Prediction confidence returned with the analysis."
        />

        <MetricCard
          label="Datasets"
          value={datasetCount}
          description="Datasets included in this analysis."
        />

        <MetricCard
          label="Indicators"
          value={indicatorCount}
          description="Analysis indicators included in the result."
        />
      </div>
    </section>
  )
}

export default ResultSummary
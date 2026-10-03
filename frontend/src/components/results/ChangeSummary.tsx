import type { ChangeMetric } from '../../types/analysisResult'

type ChangeSummaryProps = {
  changes: ChangeMetric[]
}

function formatValue(
  value: number | null,
  unit: string | null,
) {
  if (value === null) {
    return 'Unavailable'
  }

  return unit ? `${value} ${unit}` : `${value}`
}

function ChangeSummary({ changes }: ChangeSummaryProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Change Summary
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Before and After Comparison
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Comparison values returned for the selected watershed
          indicators.
        </p>
      </div>

      {changes.length > 0 ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {changes.map((metric) => (
            <article
              key={metric.id}
              className="rounded-xl border border-slate-800 bg-slate-950/40 p-5"
            >
              <h3 className="font-semibold text-white">
                {metric.label}
              </h3>

              <div className="mt-5 grid grid-cols-3 gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Before
                  </p>

                  <p className="mt-2 text-sm font-semibold text-slate-200">
                    {formatValue(metric.before, metric.unit)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    After
                  </p>

                  <p className="mt-2 text-sm font-semibold text-slate-200">
                    {formatValue(metric.after, metric.unit)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Change
                  </p>

                  <p className="mt-2 text-sm font-semibold text-emerald-400">
                    {formatValue(metric.change, metric.unit)}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-5">
          <p className="text-sm text-slate-500">
            Change measurements are unavailable.
          </p>
        </div>
      )}
    </section>
  )
}

export default ChangeSummary
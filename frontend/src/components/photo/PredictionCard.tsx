type PredictionData = {
  predictedClass: string
  confidence: number | null
  verificationRequired: boolean
  modelVersion: string | null
  warnings: string[]
}

type PredictionCardProps = {
  prediction: PredictionData | null
  isLoading?: boolean
}

function PredictionCard({
  prediction,
  isLoading = false,
}: PredictionCardProps) {
  if (isLoading) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          AI Prediction
        </p>

        <h2 className="mt-2 text-lg font-semibold text-white">
          Analyzing Photo
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          Waiting for the prediction service to return a result.
        </p>

        <div className="mt-5 space-y-3">
          <div className="h-4 w-2/3 animate-pulse rounded bg-slate-800" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-slate-800" />
          <div className="h-4 w-3/4 animate-pulse rounded bg-slate-800" />
        </div>
      </section>
    )
  }

  if (!prediction) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
          AI Prediction
        </p>

        <h2 className="mt-2 text-lg font-semibold text-white">
          Prediction Pending
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          A prediction will appear here after the uploaded photo is processed
          by the prediction service.
        </p>

        <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-sm text-slate-500">
            No prediction has been generated.
          </p>
        </div>
      </section>
    )
  }

  const confidence =
    prediction.confidence === null
      ? 'Unavailable'
      : `${(prediction.confidence * 100).toFixed(1)}%`

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            AI Prediction
          </p>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Prediction Result
          </h2>
        </div>

        <span
          className={`w-fit rounded-full border px-2.5 py-1 text-xs font-medium ${
            prediction.verificationRequired
              ? 'border-amber-500/20 bg-amber-500/10 text-amber-300'
              : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
          }`}
        >
          {prediction.verificationRequired
            ? 'Verification required'
            : 'Verification not required'}
        </span>
      </div>

      <div className="mt-6 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-emerald-400">
          Predicted Class
        </p>

        <p className="mt-2 text-2xl font-bold text-white">
          {prediction.predictedClass}
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Confidence
          </p>

          <p className="mt-2 text-sm font-semibold text-slate-200">
            {confidence}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Model Version
          </p>

          <p className="mt-2 text-sm font-semibold text-slate-200">
            {prediction.modelVersion ?? 'Unavailable'}
          </p>
        </div>
      </div>

      {prediction.warnings.length > 0 && (
        <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <p className="text-sm font-semibold text-amber-300">
            Prediction warning
          </p>

          <ul className="mt-2 space-y-1 text-sm leading-6 text-amber-200/80">
            {prediction.warnings.map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 text-xs leading-5 text-slate-500">
        AI predictions should be reviewed together with the available field and
        geospatial information.
      </p>
    </section>
  )
}

export type { PredictionData }
export default PredictionCard
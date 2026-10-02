import { useParams } from 'react-router-dom'

function AnalysisDetailsPage() {
  const { analysisId } = useParams()

  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
        Analysis Results
      </p>

      <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
        Analysis Details
      </h1>

      <p className="mt-3 max-w-2xl leading-7 text-slate-400">
        Review the results, spatial outputs, warnings, and report for this
        watershed analysis.
      </p>

      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm text-slate-500">Analysis ID</p>

        <p className="mt-2 font-mono text-lg font-semibold text-emerald-400">
          {analysisId ?? 'Unavailable'}
        </p>

        <p className="mt-4 text-sm leading-6 text-slate-400">
          Detailed metrics, charts, raster layers, and report controls will be
          implemented in later phases.
        </p>
      </div>
    </section>
  )
}

export default AnalysisDetailsPage
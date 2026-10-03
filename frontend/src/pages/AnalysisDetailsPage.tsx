import { Link, useParams } from 'react-router-dom'

import { useAnalysis } from '../context/useAnalysis'
import {
  mockDatasets,
  mockIndicators,
} from '../mocks/analysisMockData'

function AnalysisDetailsPage() {
  const { analysisId: routeAnalysisId } = useParams()

  const {
    analysisId,
    prediction,
    confirmedPolygon,
    datasetIds,
    indicators,
  } = useAnalysis()

  const isCurrentMockAnalysis =
    Boolean(routeAnalysisId) &&
    routeAnalysisId === analysisId

  const selectedDatasets = mockDatasets.filter((dataset) =>
    datasetIds.includes(dataset.id),
  )

  const selectedIndicators = mockIndicators.filter((indicator) =>
    indicators.includes(indicator.id),
  )

  if (!isCurrentMockAnalysis) {
    return (
      <div className="space-y-6">
        <section>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Results
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Analysis Session Unavailable
          </h1>

          <p className="mt-3 max-w-2xl leading-7 text-slate-400">
            This mock analysis is not available in the current frontend
            session. Mock workflow state is currently stored in memory and
            is not restored after a page refresh or direct URL visit.
          </p>
        </section>

        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
          <p className="text-sm font-semibold text-amber-300">
            Requested analysis ID
          </p>

          <p className="mt-2 break-all font-mono text-sm text-amber-200/80">
            {routeAnalysisId ?? 'Unavailable'}
          </p>
        </div>

        <Link
          to="/new-analysis"
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
        >
          Start New Analysis
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <section>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Results
          </p>

          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
            Mock Result
          </span>
        </div>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Watershed Analysis Summary
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Review the configuration and mock outputs produced by the
          frontend demonstration workflow.
        </p>

        <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
          <p className="text-sm leading-6 text-amber-200/80">
            This page contains frontend mock data only. No real watershed
            processing, satellite analysis, or backend computation has
            been performed.
          </p>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Status
          </p>

          <p className="mt-2 text-lg font-semibold text-emerald-400">
            Completed
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Datasets
          </p>

          <p className="mt-2 text-lg font-semibold text-white">
            {selectedDatasets.length}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Indicators
          </p>

          <p className="mt-2 text-lg font-semibold text-white">
            {selectedIndicators.length}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Study Area
          </p>

          <p className="mt-2 text-lg font-semibold text-white">
            {confirmedPolygon ? 'Confirmed' : 'Unavailable'}
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Analysis Identifier
        </p>

        <p className="mt-3 break-all font-mono text-lg font-semibold text-white">
          {routeAnalysisId ?? 'Unavailable'}
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            AI Prediction
          </p>

          <h2 className="mt-2 text-xl font-semibold text-white">
            {prediction?.predictedClass ?? 'Unavailable'}
          </h2>

          {prediction ? (
            <div className="mt-5 space-y-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">
                  Confidence
                </span>

                <span className="font-medium text-slate-200">
                  {prediction.confidence !== null
                   ? `${(prediction.confidence * 100).toFixed(0)}%`
                  : 'Unavailable'}
                </span>
              </div>

              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">
                  Verification
                </span>

                <span className="font-medium text-slate-200">
                  {prediction.verificationRequired
                    ? 'Required'
                    : 'Not required'}
                </span>
              </div>

              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">
                  Model
                </span>

                <span className="font-mono text-xs text-slate-300">
                  {prediction.modelVersion}
                </span>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">
              Prediction information is unavailable.
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Study Area
          </p>

          <h2 className="mt-2 text-xl font-semibold text-white">
            Confirmed Polygon
          </h2>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            {confirmedPolygon
              ? `${confirmedPolygon.coordinates.length} polygon vertices are stored in the current analysis session.`
              : 'Confirmed study-area geometry is unavailable.'}
          </p>

          <p className="mt-4 text-xs leading-5 text-slate-500">
            Detailed spatial result layers will be introduced in later
            frontend phases.
          </p>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Selected Datasets
          </p>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Analysis Timeline
          </h2>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {selectedDatasets.length > 0 ? (
            selectedDatasets.map((dataset) => (
              <article
                key={dataset.id}
                className="rounded-xl border border-slate-800 bg-slate-950/50 p-5"
              >
                <p className="font-semibold text-white">
                  {dataset.displayName}
                </p>

                <div className="mt-4 space-y-2 text-sm">
                  <p className="text-slate-400">
                    Year:{' '}
                    <span className="text-slate-200">
                      {dataset.year}
                    </span>
                  </p>

                  <p className="text-slate-400">
                    Acquisition:{' '}
                    <span className="text-slate-200">
                      {dataset.acquisitionDate ?? 'Unavailable'}
                    </span>
                  </p>

                  <p className="text-slate-400">
                    Resolution:{' '}
                    <span className="text-slate-200">
                      {dataset.resolution ?? 'Unavailable'}
                    </span>
                  </p>
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              Dataset information is unavailable.
            </p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Selected Indicators
        </p>

        <div className="mt-4 flex flex-wrap gap-3">
          {selectedIndicators.length > 0 ? (
            selectedIndicators.map((indicator) => (
              <span
                key={indicator.id}
                className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm font-medium text-emerald-300"
              >
                {indicator.displayName}
              </span>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              Indicator information is unavailable.
            </p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/30 p-6">
        <h2 className="text-lg font-semibold text-white">
          Detailed Results Coming Next
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Detailed watershed metrics, change charts, raster result
          layers, warnings, and report controls are intentionally not
          included in this mock summary. They will be implemented in
          the dedicated results phases.
        </p>
      </section>

      <div className="flex flex-wrap gap-3">
        <Link
          to="/new-analysis"
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
        >
          Back to Analysis
        </Link>

        <Link
          to="/dashboard"
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-600 hover:bg-slate-800"
        >
          Dashboard
        </Link>
      </div>
    </div>
  )
}

export default AnalysisDetailsPage
import { Link, useParams } from 'react-router-dom'

import ComparisonChart from '../components/charts/ComparisonChart'
import TimeSeriesChart from '../components/charts/TimeSeriesChart'
import RasterResultMap from '../components/map/RasterResultMap'
import ChangeSummary from '../components/results/ChangeSummary'
import MetricCard from '../components/results/MetricCard'
import ReportDownload from '../components/results/ReportDownload'
import ResultsTable from '../components/results/ResultsTable'
import ResultSummary from '../components/results/ResultSummary'
import WarningsPanel from '../components/results/WarningsPanel'
import { useAnalysis } from '../context/useAnalysis'
import { mockIndicators } from '../mocks/analysisMockData'
import { mockAnalysisResult } from '../mocks/analysisResultMockData'

function AnalysisDetailsPage() {
  const { analysisId: routeAnalysisId } = useParams()

  const {
    analysisId,
    prediction,
    datasetIds,
    selectedDatasets,
    indicators,
  } = useAnalysis()

  const isCurrentMockAnalysis =
    Boolean(routeAnalysisId) &&
    routeAnalysisId === analysisId

  /*
   * selectedDatasets contains the real metadata returned by
   * the backend dataset catalogue for the user's selection.
   *
   * datasetIds remains the authoritative selection.
   */
  const realSelectedDatasets = selectedDatasets.filter(
    (dataset) => datasetIds.includes(dataset.id),
  )

  const selectedIndicators = mockIndicators.filter(
    (indicator) =>
      indicators.includes(indicator.id),
  )

  /*
   * IMPORTANT:
   *
   * These rows are demonstration scientific results only.
   * They are intentionally NOT matched to the real backend
   * dataset IDs.
   *
   * Real uploaded/catalogue datasets must not be associated
   * with NDVI or water-area values until the backend analysis
   * service actually computes and returns those measurements.
   */
  const demoDatasetResults =
    mockAnalysisResult.datasetResults

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
            This mock analysis is not available in the current
            frontend session. Mock workflow state is currently
            stored in memory and is not restored after a page
            refresh or direct URL visit.
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
          Watershed Results Dashboard
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Review the selected real dataset configuration
          alongside demonstration scientific results,
          quality information, provenance, charts, and
          geospatial result layers.
        </p>

        <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
          <p className="text-sm leading-6 text-amber-200/80">
            Dataset configuration shown on this page comes
            from the real backend catalogue. Scientific
            measurements, changes, charts, AI output, and
            result layers remain frontend demonstration data.
            No real watershed processing, satellite analysis,
            or backend scientific computation has been
            performed.
          </p>
        </div>
      </section>

      <ResultSummary
        predictedClass={
          prediction
            ? prediction.predictedClass
            : mockAnalysisResult.prediction.predictedClass
        }
        confidence={
          prediction
            ? prediction.confidence
            : mockAnalysisResult.prediction.confidence
        }
        datasetCount={datasetIds.length}
        indicatorCount={selectedIndicators.length}
      />

      <section className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Real Backend Configuration
            </p>

            <h2 className="mt-1 text-xl font-semibold text-white">
              Selected Datasets
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              These are the actual dataset catalogue records
              selected for this analysis workflow. The
              scientific demo values shown later on this page
              have not been calculated from these datasets.
            </p>
          </div>

          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            {datasetIds.length} selected
          </span>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {realSelectedDatasets.length > 0 ? (
            realSelectedDatasets.map((dataset) => (
              <div
                key={dataset.id}
                className="rounded-xl border border-slate-800 bg-slate-950/40 p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-200">
                      {dataset.displayName}
                    </p>

                    <p className="mt-1 break-all font-mono text-xs text-slate-500">
                      {dataset.id}
                    </p>
                  </div>

                  <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
                    Backend Dataset
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-600">
                      Year
                    </p>

                    <p className="mt-1 text-sm text-slate-300">
                      {dataset.year ?? 'Unavailable'}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-600">
                      Acquisition
                    </p>

                    <p className="mt-1 text-sm text-slate-300">
                      {dataset.acquisitionDate ??
                        'Unavailable'}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-600">
                      Resolution
                    </p>

                    <p className="mt-1 text-sm text-slate-300">
                      {dataset.resolution ?? 'Unavailable'}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-600">
                      Coverage
                    </p>

                    <p className="mt-1 text-sm text-slate-300">
                      {dataset.coverage ?? 'Unavailable'}
                    </p>
                  </div>
                </div>

                {dataset.supportedIndicators.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs uppercase tracking-wider text-slate-600">
                      Supported Indicators
                    </p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      {dataset.supportedIndicators.map(
                        (indicator) => (
                          <span
                            key={indicator}
                            className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-300"
                          >
                            {indicator}
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {dataset.warnings.length > 0 && (
                  <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
                    <p className="text-xs text-amber-200">
                      {dataset.warnings.length}{' '}
                      {dataset.warnings.length === 1
                        ? 'catalogue warning'
                        : 'catalogue warnings'}
                    </p>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="lg:col-span-2 rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-6">
              <p className="text-sm font-medium text-slate-300">
                Selected dataset metadata is unavailable.
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                The dataset IDs are retained, but their
                catalogue metadata is not available in the
                current frontend session.
              </p>
            </div>
          )}
        </div>
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Key Metrics
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Demo Data
            </span>
          </div>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Watershed Measurements
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            The values below are demonstration measurements
            and were not calculated from the selected backend
            datasets.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {mockAnalysisResult.metrics.map((metric) => (
            <MetricCard
              key={metric.id}
              label={metric.label}
              value={metric.value}
              unit={metric.unit}
              description={metric.description}
            />
          ))}
        </div>
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Demonstration Dataset Results
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Mock Scientific Data
            </span>
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            These rows use dedicated mock datasets and are
            shown only to demonstrate the final result-table
            interface. They do not correspond to the real
            backend datasets selected above.
          </p>
        </div>

        <ResultsTable results={demoDatasetResults} />
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Demonstration Change Summary
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Mock Scientific Data
            </span>
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Before-and-after values are frontend demonstration
            data and have not been calculated from the real
            dataset selection.
          </p>
        </div>

        <ChangeSummary changes={mockAnalysisResult.changes} />
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Visual Analysis
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Demo Data
            </span>
          </div>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Change Visualizations
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            These charts visualize the mock scientific result
            values. The frontend does not independently
            calculate watershed measurements.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {mockAnalysisResult.changes.map((change) => (
            <ComparisonChart
              key={change.id}
              change={change}
            />
          ))}
        </div>
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Time Series
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Demo Data
            </span>
          </div>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Multi-date Measurements
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            The dates and measurements in these charts belong
            to the dedicated mock result dataset. They are
            not measurements from the real backend datasets
            selected for this workflow.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <TimeSeriesChart
            results={demoDatasetResults}
            metric="ndvi"
          />

          <TimeSeriesChart
            results={demoDatasetResults}
            metric="waterArea"
          />
        </div>
      </section>

      <WarningsPanel
        warnings={mockAnalysisResult.warnings}
        quality={mockAnalysisResult.quality}
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Provenance
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Result Source
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Source
            </p>

            <p className="mt-2 text-sm font-medium text-slate-200">
              {mockAnalysisResult.provenance.source ??
                'Unavailable'}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Model Version
            </p>

            <p className="mt-2 font-mono text-sm text-slate-200">
              {prediction?.modelVersion ??
                mockAnalysisResult.provenance
                  .modelVersion ??
                'Unavailable'}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Generated At
            </p>

            <p className="mt-2 text-sm font-medium text-slate-200">
              {mockAnalysisResult.provenance.generatedAt ??
                'Unavailable'}
            </p>
          </div>
        </div>
      </section>

      <ReportDownload />

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Analysis Configuration
        </p>

        <div className="mt-5 grid gap-6 lg:grid-cols-2">
          <div>
            <h2 className="font-semibold text-white">
              Selected Datasets
            </h2>

            <div className="mt-3 space-y-2">
              {realSelectedDatasets.length > 0 ? (
                realSelectedDatasets.map((dataset) => (
                  <div
                    key={dataset.id}
                    className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3"
                  >
                    <p className="text-sm font-medium text-slate-200">
                      {dataset.displayName}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {dataset.year ?? 'Unavailable'}
                      {' · '}
                      {dataset.acquisitionDate ??
                        'Unavailable'}
                    </p>

                    <p className="mt-1 text-xs text-slate-600">
                      {dataset.resolution ??
                        'Resolution unavailable'}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">
                  Dataset information is unavailable.
                </p>
              )}
            </div>
          </div>

          <div>
            <h2 className="font-semibold text-white">
              Selected Indicators
            </h2>

            <div className="mt-3 flex flex-wrap gap-2">
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
          </div>
        </div>
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Geospatial Result Layers
            </p>

            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
              Demo Result State
            </span>
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Raster result layers will appear here when the
            analysis backend returns real layer descriptors.
          </p>
        </div>

        <RasterResultMap
          layers={mockAnalysisResult.layers}
        />
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
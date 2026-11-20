import { useEffect, useState } from 'react'
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
import {
  getAnalysis,
  getReportDownloadUrl,
  mapAnalysisResponseToResult,
} from '../services/analysisApi'
import type { AnalysisResult } from '../types/analysisResult'

function AnalysisDetailsPage() {
  const { analysisId: routeAnalysisId } = useParams()

  const {
    analysisId,
    prediction,
    datasetIds,
    indicators,
  } = useAnalysis()

  const [realResult, setRealResult] = useState<AnalysisResult | null>(null)
  const [isLoading, setIsLoading] = useState(Boolean(routeAnalysisId))
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    if (!routeAnalysisId) {
      setIsLoading(false)
      return
    }

    if (routeAnalysisId === 'mock-analysis') {
      setRealResult(mockAnalysisResult)
      setIsLoading(false)
      return
    }

    let isActive = true
    setIsLoading(true)
    setLoadError(null)

    getAnalysis(routeAnalysisId)
      .then((data) => {
        if (!isActive) return
        if (data.status === 'completed') {
          setRealResult(mapAnalysisResponseToResult(data))
        } else if (data.status === 'failed') {
          setLoadError(data.error?.message || 'Analysis processing failed.')
        } else {
          setLoadError(
            `Analysis status is currently '${data.status}'. Processing is underway.`,
          )
        }
      })
      .catch((err) => {
        if (!isActive) return
        // Fall back to in-memory mock result if route matches active session
        if (routeAnalysisId === analysisId) {
          setRealResult(mockAnalysisResult)
        } else {
          setLoadError(
            err instanceof Error ? err.message : 'Analysis could not be found.',
          )
        }
      })
      .finally(() => {
        if (isActive) setIsLoading(false)
      })

    return () => {
      isActive = false
    }
  }, [routeAnalysisId, analysisId])

  const activeResult = realResult ?? mockAnalysisResult


  const selectedIndicators = mockIndicators.filter((indicator) => {
    if (indicators.includes(indicator.id)) return true
    if (indicator.id === 'vegetation' && indicators.includes('ndvi')) return true
    if (
      indicator.id === 'surface-water' &&
      (indicators.includes('water') || indicators.includes('mndwi'))
    ) {
      return true
    }
    return false
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <section>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Results
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Loading Analysis Results...
          </h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-400">
            Fetching computed vegetation metrics, surface water changes, and map layers from the backend.
          </p>
        </section>
        <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
          <p className="text-sm text-slate-300">Retrieving persisted analysis {routeAnalysisId}...</p>
        </div>
      </div>
    )
  }

  if (loadError && !realResult) {
    return (
      <div className="space-y-6">
        <section>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Results
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Analysis Unavailable
          </h1>

          <p className="mt-3 max-w-2xl leading-7 text-slate-400">
            {loadError}
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

  const isRealBackendData = Boolean(realResult && routeAnalysisId !== 'mock-analysis')

  return (
    <div className="space-y-8">
      <section>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Results
          </p>

          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
              isRealBackendData
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
            }`}
          >
            {isRealBackendData ? 'Verified Scientific Results' : 'Mock Result'}
          </span>
        </div>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Watershed Results Dashboard
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          {isRealBackendData
            ? 'Review computed vegetation indices, surface water changes, and georeferenced raster result layers from Sentinel-2 satellite observations.'
            : 'Review demonstration scientific results, quality information, provenance, charts, and geospatial result layers.'}
        </p>

        {isRealBackendData ? (
          <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
            <p className="text-sm leading-6 text-emerald-200/90">
              Analysis verified from authentic Sentinel-2 Level-2A surface reflectance data, cloud-shadow SCL quality filtering, and common spatial support grid.
            </p>
          </div>
        ) : (
          <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
            <p className="text-sm leading-6 text-amber-200/80">
              Demonstration mode active. Values shown are simulated.
            </p>
          </div>
        )}
      </section>

      <ResultSummary
        predictedClass={
          activeResult.prediction.predictedClass ??
          (prediction ? prediction.predictedClass : 'Check Dam')
        }
        confidence={
          activeResult.prediction.confidence ??
          (prediction ? prediction.confidence : null)
        }
        datasetCount={activeResult.datasetResults.length || datasetIds.length || 2}
        indicatorCount={selectedIndicators.length || 2}
      />

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Key Metrics
            </p>
            <span
              className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
                isRealBackendData
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
              }`}
            >
              {isRealBackendData ? 'Persisted Data' : 'Demo Data'}
            </span>
          </div>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Watershed Measurements
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Quantitative environmental index changes computed across observations.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {activeResult.metrics.map((metric) => (
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
              Dataset Chronological Results
            </p>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Per-observation measurements computed on the common valid study area.
          </p>
        </div>

        <ResultsTable results={activeResult.datasetResults} />
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Change Summary
            </p>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Before-and-after change metrics derived from the earliest and latest observation dates.
          </p>
        </div>

        <ChangeSummary changes={activeResult.changes} />
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Visual Analysis
            </p>
          </div>
          <h2 className="mt-1 text-xl font-semibold text-white">
            Change Visualizations
          </h2>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {activeResult.changes.map((change) => (
            <ComparisonChart key={change.id} change={change} />
          ))}
        </div>
      </section>

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Time Series
            </p>
          </div>
          <h2 className="mt-1 text-xl font-semibold text-white">
            Multi-date Measurements
          </h2>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <TimeSeriesChart
            results={activeResult.datasetResults}
            metric="ndvi"
          />
          <TimeSeriesChart
            results={activeResult.datasetResults}
            metric="waterArea"
          />
        </div>
      </section>

      <WarningsPanel
        warnings={activeResult.warnings}
        quality={activeResult.quality}
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Provenance
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Result Source & Pipeline Metadata
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Source
            </p>
            <p className="mt-2 text-sm font-medium text-slate-200">
              {activeResult.provenance.source ?? 'Sentinel-2 L2A Multispectral'}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Model Version
            </p>
            <p className="mt-2 font-mono text-sm text-slate-200">
              {activeResult.provenance.modelVersion ?? 'production-v1'}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Generated At
            </p>
            <p className="mt-2 text-sm font-medium text-slate-200">
              {activeResult.provenance.generatedAt ?? 'Unavailable'}
            </p>
          </div>
        </div>
      </section>

      <ReportDownload
        available={Boolean(routeAnalysisId)}
        onDownload={() => {
          if (routeAnalysisId) {
            window.open(getReportDownloadUrl(routeAnalysisId), '_blank')
          }
        }}
      />

      <section>
        <div className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Geospatial Result Layers
            </p>
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-300">
              {activeResult.layers.length} Layers Available
            </span>
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Interactive map overlay visualizing analytical NDVI and MNDWI surface water layers.
          </p>
        </div>

        <RasterResultMap
          layers={activeResult.layers}
          datasetResults={activeResult.datasetResults}
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

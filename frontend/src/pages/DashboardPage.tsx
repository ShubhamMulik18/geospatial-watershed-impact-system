import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import DashboardSummary from '../components/dashboard/DashboardSummary'
import QuickActions from '../components/dashboard/QuickActions'
import RecentAnalyses from '../components/dashboard/RecentAnalyses'
import { listRecentAnalyses, type AnalysisResponse } from '../services/analysisApi'
import { getDatasets } from '../services/datasetApi'

function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([])
  const [datasetsCount, setDatasetsCount] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [datasetError, setDatasetError] = useState<string | null>(null)

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    setDatasetError(null)

    try {
      const [analysesRes, datasetsRes] = await Promise.all([
        listRecentAnalyses(),
        getDatasets().catch(() => {
          setDatasetError('Failed to load dataset catalogue.')
          return []
        }),
      ])

      setAnalyses(analysesRes)
      setDatasetsCount(datasetsRes.length)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to connect to backend service. Please verify backend is running on port 8000.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const totalAnalyses = analyses.length
  const completedAnalyses = analyses.filter(
    (a) => a.status.toLowerCase() === 'completed',
  ).length
  const processingAnalyses = analyses.filter(
    (a) =>
      a.status.toLowerCase() === 'running' ||
      a.status.toLowerCase() === 'pending' ||
      a.status.toLowerCase() === 'processing',
  ).length

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Overview
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Watershed Dashboard
          </h1>

          <p className="mt-3 max-w-2xl leading-7 text-slate-400">
            Monitor geospatial watershed analyses, review recent activity, and access
            verified satellite observation pipelines.
          </p>
        </div>

        <Link
          to="/new-analysis"
          className="inline-flex w-fit items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/10 transition hover:bg-emerald-400"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              d="M12 5v14M5 12h14"
            />
          </svg>

          New Analysis
        </Link>
      </section>

      {datasetError && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-5 py-3 text-sm text-amber-300">
          {datasetError}
        </div>
      )}

      <DashboardSummary
        total={totalAnalyses}
        completed={completedAnalyses}
        processing={processingAnalyses}
        datasets={datasetsCount}
        isLoading={isLoading}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <RecentAnalyses
          analyses={analyses}
          isLoading={isLoading}
          error={error}
          onRetry={fetchDashboardData}
        />

        <QuickActions />
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
            <p className="text-xs font-medium text-slate-300">
              System Active: Connected to PostgreSQL & Sentinel-2 Pipeline Service
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">
            v2.4 Production Engine
          </span>
        </div>
      </section>
    </div>
  )
}

export default DashboardPage

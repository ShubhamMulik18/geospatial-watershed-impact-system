import {
  useEffect,
  useRef,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import AnalysisControls, {
  type AnalysisMode,
} from '../components/analysis/AnalysisControls'
import DatasetSelector from '../components/analysis/DatasetSelector'
import IndicatorSelector from '../components/analysis/IndicatorSelector'
import ProcessingStatus, {
  type ProcessingState,
} from '../components/analysis/ProcessingStatus'
import ValidationErrors from '../components/analysis/ValidationErrors'
import AnalysisMap from '../components/map/AnalysisMap'
import PhotoMetadata, {
  type PhotoMetadataData,
} from '../components/photo/PhotoMetadata'
import PhotoPreview from '../components/photo/PhotoPreview'
import PhotoUploader from '../components/photo/PhotoUploader'
import PredictionCard from '../components/photo/PredictionCard'
import { useAnalysis } from '../context/useAnalysis'
import {
  mockAnalysisModes,
  mockDatasets,
  mockIndicators,
  mockPrediction,
} from '../mocks/analysisMockData'

const unavailableMetadata: PhotoMetadataData = {
  latitude: null,
  longitude: null,
  capturedAt: null,
  cameraMake: null,
  cameraModel: null,
}

const mockPhotoMetadata: PhotoMetadataData = {
  latitude: null,
  longitude: null,
  capturedAt: null,
  cameraMake: null,
  cameraModel: null,
}

function NewAnalysisPage() {
  const {
    photoMetadata,
    prediction,
    confirmedPolygon,
    datasetIds,
    indicators,
    analysisId,
    isSubmitting,

    setPhoto,
    setPrediction,
    setDatasetIds,
    setIndicators,
    setAnalysisId,

    markValidationFresh,
    markResultsFresh,

    beginPhotoRequest,
    isCurrentPhotoRequest,

    beginSubmission,
    finishSubmission,

    resetAnalysis,
  } = useAnalysis()

  const [selectedPhoto, setSelectedPhoto] =
    useState<File | null>(null)

  const [previewUrl, setPreviewUrl] =
    useState<string | null>(null)

  const [selectedAnalysisMode, setSelectedAnalysisMode] =
    useState<AnalysisMode | null>(null)

  const [isPredictionLoading, setIsPredictionLoading] =
    useState(false)

  const [processingStatus, setProcessingStatus] =
    useState<ProcessingState>('idle')

  const [processingMessage, setProcessingMessage] =
    useState<string | null>(null)

  const previewUrlRef = useRef<string | null>(null)

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
      }
    }
  }, [])

  async function wait(milliseconds: number) {
    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, milliseconds)
    })
  }

  async function handlePhotoSelect(file: File) {
    const requestId = beginPhotoRequest()

    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }

    const objectUrl = URL.createObjectURL(file)

    previewUrlRef.current = objectUrl

    setSelectedPhoto(file)
    setPreviewUrl(objectUrl)

    setSelectedAnalysisMode(null)
    setProcessingStatus('idle')
    setProcessingMessage(null)

    /*
     * Phase 10/11 mock workflow:
     * this is not a real backend photo ID or extracted EXIF metadata.
     */
    setPhoto(
      `mock-photo-${requestId}`,
      mockPhotoMetadata,
    )

    setIsPredictionLoading(true)

    await wait(700)

    if (!isCurrentPhotoRequest(requestId)) {
      return
    }

    setPrediction(
      `mock-prediction-${requestId}`,
      mockPrediction,
    )

    setIsPredictionLoading(false)
  }

  function handlePhotoRemove() {
    /*
     * Starting a new photo request invalidates any late response
     * belonging to the photo being removed.
     */
    beginPhotoRequest()

    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }

    previewUrlRef.current = null

    setSelectedPhoto(null)
    setPreviewUrl(null)

    setSelectedAnalysisMode(null)
    setIsPredictionLoading(false)

    setProcessingStatus('idle')
    setProcessingMessage(null)

    resetAnalysis()
  }

  const validationErrors: string[] = []

  if (!selectedPhoto) {
    validationErrors.push(
      'Upload a field photo to begin the mock analysis workflow.',
    )
  }

  if (!confirmedPolygon) {
    validationErrors.push(
      'Draw and confirm a valid study area polygon.',
    )
  }

  if (datasetIds.length < 2) {
    validationErrors.push(
      'Select at least two distinct compatible datasets.',
    )
  }

  if (indicators.length === 0) {
    validationErrors.push(
      'Select at least one supported analysis indicator.',
    )
  }

  if (!selectedAnalysisMode) {
    validationErrors.push(
      'Select an available comparison mode.',
    )
  }

  const canStartAnalysis =
    validationErrors.length === 0 &&
    !isSubmitting

  async function handleStartAnalysis() {
    if (!canStartAnalysis) {
      return
    }

    const requestId = beginSubmission()

    if (requestId === null) {
      return
    }

    setProcessingStatus('created')
    setProcessingMessage(
      'Mock analysis request created.',
    )

    await wait(600)

    setProcessingStatus('validating')
    setProcessingMessage(
      'Validating the mock analysis configuration.',
    )

    await wait(700)

    setProcessingStatus('processing')
    setProcessingMessage(
      'Running the mock watershed analysis.',
    )

    await wait(1200)

    /*
     * finishSubmission rejects a response belonging to an
     * invalidated or older analysis request.
     */
    const isCurrentRequest =
      finishSubmission(requestId)

    if (!isCurrentRequest) {
      return
    }

    setAnalysisId(
      `mock-analysis-${requestId}`,
    )

    markValidationFresh()
    markResultsFresh()

    setProcessingStatus('completed')
    setProcessingMessage(
      'Mock analysis completed successfully. No real backend processing was performed.',
    )
  }

  return (
    <div className="space-y-8">
      <section>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Workspace
          </p>

          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
            Mock Mode
          </span>
        </div>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          New Watershed Analysis
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Configure a watershed impact assessment using field evidence,
          a confirmed study area, compatible geospatial datasets, and
          supported analysis indicators.
        </p>

        <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
          <p className="text-sm leading-6 text-amber-200/80">
            Frontend demonstration mode is active. Dataset records,
            AI prediction, identifiers, and processing states shown in
            this workflow are mock data and are not backend results.
          </p>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            Step 1
          </p>

          <p className="mt-1 text-sm font-semibold text-emerald-200">
            Field Photo
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            Step 2
          </p>

          <p className="mt-1 text-sm font-semibold text-emerald-200">
            Study Area
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            Step 3
          </p>

          <p className="mt-1 text-sm font-semibold text-emerald-200">
            Datasets
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            Step 4
          </p>

          <p className="mt-1 text-sm font-semibold text-emerald-200">
            Analysis
          </p>
        </div>
      </section>

      {!selectedPhoto || !previewUrl ? (
        <PhotoUploader
          onFileSelect={handlePhotoSelect}
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
          <PhotoPreview
            file={selectedPhoto}
            previewUrl={previewUrl}
            onRemove={handlePhotoRemove}
          />

          <div className="space-y-6">
            <PhotoMetadata
              metadata={
                photoMetadata ??
                unavailableMetadata
              }
            />

            <PredictionCard
              prediction={prediction}
              isLoading={isPredictionLoading}
            />
          </div>
        </div>
      )}

      <AnalysisMap location={null} />

      <section>
        <div className="mb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Dataset Configuration
          </p>

          <h2 className="mt-1 text-2xl font-semibold text-white">
            Configure Analysis Data
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            The options below are mock catalogue records provided only
            to exercise the complete frontend workflow before backend
            integration.
          </p>
        </div>

        <div className="space-y-6">
          <DatasetSelector
            datasets={mockDatasets}
            selectedDatasetIds={datasetIds}
            onSelectionChange={setDatasetIds}
          />

          <IndicatorSelector
            indicators={mockIndicators}
            selectedIndicatorIds={indicators}
            onSelectionChange={setIndicators}
          />

          <AnalysisControls
            modes={mockAnalysisModes}
            selectedMode={selectedAnalysisMode}
            onModeChange={setSelectedAnalysisMode}
          />
        </div>
      </section>

      <ValidationErrors
        errors={validationErrors}
      />

      <ProcessingStatus
        status={processingStatus}
        message={processingMessage}
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Mock Analysis
            </p>

            <h2 className="mt-1 text-lg font-semibold text-white">
              Start Analysis
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              The button becomes available after the photo, confirmed
              polygon, dataset, indicator, and comparison-mode
              requirements are satisfied.
            </p>

            {analysisId && (
              <p className="mt-3 text-xs text-emerald-300">
                Mock analysis ID: {analysisId}
              </p>
            )}
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-3">
            <button
              type="button"
              disabled={!canStartAnalysis}
              onClick={handleStartAnalysis}
              className="inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
            >
              {isSubmitting
                ? 'Analysis Running...'
                : 'Start Mock Analysis'}
            </button>

            {analysisId &&
              processingStatus === 'completed' && (
                <Link
                  to={`/analyses/${analysisId}`}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-3 text-sm font-semibold text-emerald-300 transition hover:border-emerald-400/50 hover:bg-emerald-500/15 hover:text-emerald-200"
                >
                  View Mock Results

                  <svg
                    viewBox="0 0 24 24"
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 12h14m-6-6 6 6-6 6"
                    />
                  </svg>
                </Link>
              )}
          </div>
        </div>
      </section>
    </div>
  )
}

export default NewAnalysisPage
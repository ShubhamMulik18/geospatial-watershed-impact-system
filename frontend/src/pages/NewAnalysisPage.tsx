import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import AnalysisControls, {
  type AnalysisMode,
} from '../components/analysis/AnalysisControls'
import DatasetSelector from '../components/analysis/DatasetSelector'
import DatasetUploader from '../components/analysis/DatasetUploader'
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
  mockIndicators,
  mockPrediction,
} from '../mocks/analysisMockData'
import { getDatasets } from '../services/datasetApi'
import { uploadPhoto } from '../services/photoApi'

const unavailableMetadata: PhotoMetadataData = {
  latitude: null,
  longitude: null,
  capturedAt: null,
  exifStatus: 'missing',
  warnings: [],
}

function NewAnalysisPage() {
  const {
    photoId,
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
    setSelectedDatasets,
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

  const [isPhotoUploading, setIsPhotoUploading] =
    useState(false)

  const [photoUploadError, setPhotoUploadError] =
    useState<string | null>(null)

  const [datasets, setDatasets] = useState<
    Awaited<ReturnType<typeof getDatasets>>
  >([])

  const [isDatasetsLoading, setIsDatasetsLoading] =
    useState(true)

  const [datasetsError, setDatasetsError] =
    useState<string | null>(null)

  const [isPredictionLoading, setIsPredictionLoading] =
    useState(false)

  const [processingStatus, setProcessingStatus] =
    useState<ProcessingState>('idle')

  const [processingMessage, setProcessingMessage] =
    useState<string | null>(null)

  const previewUrlRef = useRef<string | null>(null)

  /*
   * Phase 11 catalogue synchronisation.
   *
   * The backend catalogue is the source of truth for
   * available dataset IDs and their real metadata.
   *
   * If a selected dataset disappears from the catalogue,
   * remove the stale ID and keep selected dataset metadata
   * synchronized with the remaining valid IDs.
   */
  const reconcileDatasetSelection = useCallback(
    (
      catalogue: Awaited<ReturnType<typeof getDatasets>>,
    ) => {
      const availableDatasetIds = new Set(
        catalogue.map((dataset) => dataset.id),
      )

      const validDatasetIds = datasetIds.filter(
        (datasetId) =>
          availableDatasetIds.has(datasetId),
      )

      const validSelectedDatasets = catalogue.filter(
        (dataset) =>
          validDatasetIds.includes(dataset.id),
      )

      setSelectedDatasets(validSelectedDatasets)

      if (validDatasetIds.length !== datasetIds.length) {
        setDatasetIds(validDatasetIds)
      }
    },
    [
      datasetIds,
      setDatasetIds,
      setSelectedDatasets,
    ],
  )

  /*
   * Reload the real dataset catalogue after a successful
   * upload and reconcile the existing selection.
   */
  const loadDatasets = useCallback(async () => {
    setDatasetsError(null)

    const catalogue = await getDatasets()

    setDatasets(catalogue)
    reconcileDatasetSelection(catalogue)

    return catalogue
  }, [reconcileDatasetSelection])

  /*
   * Initial catalogue load.
   *
   * This effect intentionally runs only once when the page
   * mounts. Dataset selection changes must not trigger
   * repeated GET /api/datasets requests.
   */
  useEffect(() => {
    let isActive = true

    async function loadInitialDatasets() {
      setIsDatasetsLoading(true)
      setDatasetsError(null)

      try {
        const catalogue = await getDatasets()

        if (!isActive) {
          return
        }

        setDatasets(catalogue)
      } catch (error) {
        if (!isActive) {
          return
        }

        setDatasets([])

        setDatasetsError(
          error instanceof Error
            ? error.message
            : 'Unable to load the dataset catalogue.',
        )
      } finally {
        if (isActive) {
          setIsDatasetsLoading(false)
        }
      }
    }

    void loadInitialDatasets()

    return () => {
      isActive = false
    }
  }, [])

  /*
   * After a real dataset upload succeeds, reload the
   * catalogue from the backend and reconcile the selection.
   */
  async function handleDatasetUploadSuccess() {
    try {
      await loadDatasets()
    } catch (error) {
      setDatasetsError(
        error instanceof Error
          ? error.message
          : 'The dataset was uploaded, but the catalogue could not be refreshed.',
      )
    }
  }

  /*
   * Store both the selected IDs and the corresponding real
   * backend dataset metadata.
   *
   * Dataset IDs remain the authoritative selection used by
   * the workflow. The metadata is retained so the Results
   * page can display the actual selected dataset names,
   * dates, resolution and other catalogue information.
   */
  function handleDatasetSelectionChange(
    nextDatasetIds: string[],
  ) {
    setDatasetIds(nextDatasetIds)

    const nextSelectedDatasets = datasets.filter(
      (dataset) =>
        nextDatasetIds.includes(dataset.id),
    )

    setSelectedDatasets(nextSelectedDatasets)
  }

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
     * Clear previous photo-dependent state while the
     * newly selected photo is uploaded.
     */
    setPhoto(null, null)

    setPhotoUploadError(null)
    setIsPhotoUploading(true)

    try {
      /*
       * Real photo backend integration.
       */
      const uploadedPhoto = await uploadPhoto(file)

      /*
       * Ignore a late response if another photo was
       * selected or this photo was removed.
       */
      if (!isCurrentPhotoRequest(requestId)) {
        return
      }

      const metadata: PhotoMetadataData = {
        latitude: uploadedPhoto.latitude,
        longitude: uploadedPhoto.longitude,
        capturedAt: uploadedPhoto.capture_date,
        exifStatus: uploadedPhoto.exif_status,
        warnings: uploadedPhoto.warnings,
      }

      /*
       * Store the real backend photo ID and metadata.
       */
      setPhoto(
        uploadedPhoto.photo_id,
        metadata,
      )

      /*
       * AI inference remains mocked.
       */
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
    } catch (error) {
      if (!isCurrentPhotoRequest(requestId)) {
        return
      }

      /*
       * Failed uploads must never create a fake photo ID.
       */
      setPhoto(null, null)
      setPrediction(null, null)

      setIsPredictionLoading(false)

      setPhotoUploadError(
        error instanceof Error
          ? error.message
          : 'Photo upload failed.',
      )
    } finally {
      if (isCurrentPhotoRequest(requestId)) {
        setIsPhotoUploading(false)
      }
    }
  }

  function handlePhotoRemove() {
    /*
     * Invalidate any late backend response belonging to
     * the removed photo.
     */
    beginPhotoRequest()

    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }

    previewUrlRef.current = null

    setSelectedPhoto(null)
    setPreviewUrl(null)

    setSelectedAnalysisMode(null)

    setIsPhotoUploading(false)
    setPhotoUploadError(null)

    setIsPredictionLoading(false)

    setProcessingStatus('idle')
    setProcessingMessage(null)

    resetAnalysis()
  }

  const validationErrors: string[] = []

  if (!selectedPhoto) {
    validationErrors.push(
      'Upload a field photo to begin the analysis workflow.',
    )
  }

  if (selectedPhoto && isPhotoUploading) {
    validationErrors.push(
      'Wait for the field photo upload to complete.',
    )
  }

  if (selectedPhoto && photoUploadError) {
    validationErrors.push(
      'The selected field photo could not be uploaded.',
    )
  }

  /*
   * A selected local file is not enough.
   * The backend must successfully store the photo.
   */
  if (
    selectedPhoto &&
    !isPhotoUploading &&
    !photoUploadError &&
    !photoId
  ) {
    validationErrors.push(
      'The field photo must be successfully stored by the backend before analysis can begin.',
    )
  }

  if (!confirmedPolygon) {
    validationErrors.push(
      'Draw and confirm a valid study area polygon.',
    )
  }

  /*
   * Analysis cannot proceed while the real catalogue is
   * loading or unavailable.
   */
  if (isDatasetsLoading) {
    validationErrors.push(
      'Wait for the dataset catalogue to finish loading.',
    )
  } else if (datasetsError) {
    validationErrors.push(
      'The dataset catalogue must be available before analysis can begin.',
    )
  } else if (datasetIds.length < 2) {
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
    !isSubmitting &&
    !isPhotoUploading

  /*
   * AnalysisMap expects:
   *
   * [longitude, latitude]
   *
   * Coordinates are only used when both values were
   * returned by the backend.
   */
  const photoLocation: [number, number] | null =
    photoMetadata?.latitude != null &&
    photoMetadata?.longitude != null
      ? [
          photoMetadata.longitude,
          photoMetadata.latitude,
        ]
      : null

  async function handleStartAnalysis() {
    if (!canStartAnalysis) {
      return
    }

    const requestId = beginSubmission()

    if (requestId === null) {
      return
    }

    /*
     * Analysis execution remains mocked until the real
     * backend analysis API becomes available.
     */
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
      'Mock analysis completed successfully. No real backend analysis processing was performed.',
    )
  }

  return (
    <div className="space-y-8">
      <section>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
            Analysis Workspace
          </p>

          <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-xs font-semibold text-sky-300">
            Hybrid Integration
          </span>
        </div>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          New Watershed Analysis
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Configure a watershed impact assessment using field
          evidence, a confirmed study area, compatible
          geospatial datasets, and supported analysis
          indicators.
        </p>

        <div className="mt-5 rounded-xl border border-sky-500/20 bg-sky-500/5 px-4 py-3">
          <p className="text-sm leading-6 text-sky-200/80">
            Field photos, dataset catalogue records, and
            GeoTIFF dataset uploads are connected to the real
            backend. AI prediction, indicator processing,
            analysis execution, and results remain in
            demonstration mode until their backend
            integrations are available.
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

      {isPhotoUploading && (
        <div className="rounded-xl border border-sky-500/20 bg-sky-500/10 p-4">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-sky-300/30 border-t-sky-300" />

            <div>
              <p className="text-sm font-semibold text-sky-200">
                Uploading field photo
              </p>

              <p className="mt-1 text-sm text-sky-200/70">
                The backend is storing the photo and reading
                available EXIF metadata.
              </p>
            </div>
          </div>
        </div>
      )}

      {photoUploadError && (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-4"
        >
          <p className="text-sm font-semibold text-rose-300">
            Photo upload failed
          </p>

          <p className="mt-1 text-sm text-rose-300/80">
            {photoUploadError}
          </p>
        </div>
      )}

      <AnalysisMap location={photoLocation} />

      <section>
        <div className="mb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Dataset Configuration
          </p>

          <h2 className="mt-1 text-2xl font-semibold text-white">
            Configure Analysis Data
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Dataset catalogue records and GeoTIFF uploads are
            connected to the backend. Indicator selection and
            analysis execution remain in demonstration mode
            until their backend services are available.
          </p>
        </div>

        <div className="space-y-6">
          <DatasetUploader
            onUploadSuccess={handleDatasetUploadSuccess}
          />

          {isDatasetsLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
              <div className="flex items-center gap-3">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-300/30 border-t-emerald-300" />

                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Loading dataset catalogue
                  </p>

                  <p className="mt-1 text-sm text-slate-400">
                    Requesting available geospatial datasets
                    from the backend.
                  </p>
                </div>
              </div>
            </div>
          ) : datasetsError ? (
            <div
              role="alert"
              className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6"
            >
              <p className="font-semibold text-rose-300">
                Dataset catalogue unavailable
              </p>

              <p className="mt-2 text-sm leading-6 text-rose-300/80">
                {datasetsError}
              </p>

              <p className="mt-3 text-xs leading-5 text-slate-400">
                Make sure the FastAPI backend and database are
                running, then reload this page.
              </p>
            </div>
          ) : (
            <DatasetSelector
              datasets={datasets}
              selectedDatasetIds={datasetIds}
              onSelectionChange={
                handleDatasetSelectionChange
              }
            />
          )}

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
              Analysis
            </p>

            <h2 className="mt-1 text-lg font-semibold text-white">
              Start Analysis
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              The button becomes available after the photo
              upload, confirmed polygon, dataset, indicator,
              and comparison-mode requirements are satisfied.
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
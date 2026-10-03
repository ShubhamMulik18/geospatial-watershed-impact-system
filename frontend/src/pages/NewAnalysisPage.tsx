import { useState } from 'react'

import AnalysisControls, {
  type AnalysisMode,
  type AnalysisModeOption,
} from '../components/analysis/AnalysisControls'
import DatasetSelector from '../components/analysis/DatasetSelector'
import IndicatorSelector, {
  type IndicatorOption,
} from '../components/analysis/IndicatorSelector'
import ProcessingStatus from '../components/analysis/ProcessingStatus'
import ValidationErrors from '../components/analysis/ValidationErrors'
import AnalysisMap from '../components/map/AnalysisMap'
import PhotoMetadata, {
  type PhotoMetadataData,
} from '../components/photo/PhotoMetadata'
import PhotoPreview from '../components/photo/PhotoPreview'
import PhotoUploader from '../components/photo/PhotoUploader'
import PredictionCard from '../components/photo/PredictionCard'
import type { DatasetMetadata } from '../types/dataset'

const unavailableMetadata: PhotoMetadataData = {
  latitude: null,
  longitude: null,
  capturedAt: null,
  cameraMake: null,
  cameraModel: null,
}

// The real dataset catalogue will come from the backend.
// Keep this empty rather than inventing datasets.
const availableDatasets: DatasetMetadata[] = []

// Indicator support will be derived from the selected datasets
// and backend compatibility information.
const availableIndicators: IndicatorOption[] = []

// The backend/workflow will determine which modes are available.
const availableAnalysisModes: AnalysisModeOption[] = []

function NewAnalysisPage() {
  const [selectedPhoto, setSelectedPhoto] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([])
  const [selectedIndicatorIds, setSelectedIndicatorIds] = useState<string[]>([])
  const [selectedAnalysisMode, setSelectedAnalysisMode] =
    useState<AnalysisMode | null>(null)

  function handlePhotoSelect(file: File) {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    const objectUrl = URL.createObjectURL(file)

    setSelectedPhoto(file)
    setPreviewUrl(objectUrl)
  }

  function handlePhotoRemove() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    setSelectedPhoto(null)
    setPreviewUrl(null)
  }

  const validationErrors: string[] = []

  if (selectedDatasetIds.length < 2) {
    validationErrors.push(
      'Select at least two distinct compatible datasets.',
    )
  }

  if (selectedIndicatorIds.length === 0) {
    validationErrors.push(
      'Select at least one supported analysis indicator.',
    )
  }

  if (!selectedAnalysisMode) {
    validationErrors.push(
      'Select an available comparison mode.',
    )
  }

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
          Analysis Workspace
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          New Watershed Analysis
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Configure a watershed impact assessment using field evidence,
          a confirmed study area, compatible geospatial datasets, and
          supported analysis indicators.
        </p>
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

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Step 4
          </p>

          <p className="mt-1 text-sm font-medium text-slate-500">
            Analysis
          </p>
        </div>
      </section>

      {!selectedPhoto || !previewUrl ? (
        <PhotoUploader onFileSelect={handlePhotoSelect} />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
          <PhotoPreview
            file={selectedPhoto}
            previewUrl={previewUrl}
            onRemove={handlePhotoRemove}
          />

          <div className="space-y-6">
            <PhotoMetadata metadata={unavailableMetadata} />

            <PredictionCard prediction={null} />
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
            Select compatible datasets, supported indicators, and an
            available comparison mode. These options will be populated
            from the backend dataset workflow when integration is
            available.
          </p>
        </div>

        <div className="space-y-6">
          <DatasetSelector
            datasets={availableDatasets}
            selectedDatasetIds={selectedDatasetIds}
            onSelectionChange={setSelectedDatasetIds}
          />

          <IndicatorSelector
            indicators={availableIndicators}
            selectedIndicatorIds={selectedIndicatorIds}
            onSelectionChange={setSelectedIndicatorIds}
          />

          <AnalysisControls
            modes={availableAnalysisModes}
            selectedMode={selectedAnalysisMode}
            onModeChange={setSelectedAnalysisMode}
          />
        </div>
      </section>

      <ValidationErrors errors={validationErrors} />

      <ProcessingStatus status="idle" />

      <section className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-400">
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 19V9m5 10V5m5 14v-7m5 7V3"
              />
            </svg>
          </div>

          <div>
            <p className="font-medium text-slate-300">
              Analysis workflow
            </p>

            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
              Field-photo selection, local preview, study-area editing,
              dataset configuration, and analysis status interfaces are
              available. Backend upload, AI prediction, dataset
              catalogue data, and analysis execution will be connected
              in their respective integration phases.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default NewAnalysisPage
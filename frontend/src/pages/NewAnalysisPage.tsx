import { useState } from 'react'

import AnalysisMap from '../components/map/AnalysisMap'
import PhotoMetadata, {
  type PhotoMetadataData,
} from '../components/photo/PhotoMetadata'
import PhotoPreview from '../components/photo/PhotoPreview'
import PhotoUploader from '../components/photo/PhotoUploader'
import PredictionCard from '../components/photo/PredictionCard'

const unavailableMetadata: PhotoMetadataData = {
  latitude: null,
  longitude: null,
  capturedAt: null,
  cameraMake: null,
  cameraModel: null,
}

function NewAnalysisPage() {
  const [selectedPhoto, setSelectedPhoto] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

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
          Begin a new watershed impact assessment by providing a field
          photograph. Additional study-area, dataset, and analysis controls will
          become available in the following workflow stages.
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

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Step 2
          </p>

          <p className="mt-1 text-sm font-medium text-slate-500">
            Study Area
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Step 3
          </p>

          <p className="mt-1 text-sm font-medium text-slate-500">
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
              Photo selection and local preview are available now. Backend
              upload, AI prediction, study-area mapping, dataset selection, and
              analysis execution will be connected in their respective phases.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default NewAnalysisPage
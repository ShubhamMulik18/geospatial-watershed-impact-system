import { useState } from 'react'

import DatasetUploader from '../components/datasets/DatasetUploader'
import DatasetValidationSummary, {
  type DatasetValidationData,
} from '../components/datasets/DatasetValidationSummary'

const pendingValidation: DatasetValidationData = {
  status: 'pending',
  warnings: [],
  errors: [],
  qualityInformation: null,
}

function DatasetsPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  function handleFileSelect(file: File) {
    setSelectedFile(file)
  }

  function handleFileRemove() {
    setSelectedFile(null)
  }

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
          Data Catalogue
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Datasets
        </h1>

        <p className="mt-3 max-w-3xl leading-7 text-slate-400">
          Manage the geospatial datasets used for watershed impact
          analysis. Dataset metadata, compatibility, quality, and
          validation results will be provided by the dataset workflow.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Catalogue
          </p>

          <p className="mt-3 text-2xl font-bold text-white">
            —
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Awaiting backend catalogue
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Validated
          </p>

          <p className="mt-3 text-2xl font-bold text-white">
            —
          </p>

          <p className="mt-1 text-sm text-slate-500">
            No validation data available
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Selected File
          </p>

          <p className="mt-3 truncate text-lg font-semibold text-white">
            {selectedFile ? selectedFile.name : 'None'}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {selectedFile
              ? 'Local file only'
              : 'No local dataset selected'}
          </p>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        <DatasetUploader
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
        />

        <DatasetValidationSummary
          validation={pendingValidation}
        />
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
        <div className="border-b border-slate-800 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Dataset Catalogue
          </p>

          <h2 className="mt-1 text-lg font-semibold text-white">
            Available Datasets
          </h2>
        </div>

        <div className="p-6">
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/30 px-6 py-10 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-slate-400">
              <svg
                viewBox="0 0 24 24"
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6.5 12 3l8 3.5-8 3.5-8-3.5Zm0 5L12 15l8-3.5M4 16.5 12 20l8-3.5"
                />
              </svg>
            </div>

            <p className="mt-4 font-medium text-slate-300">
              Dataset catalogue not connected
            </p>

            <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
              Dataset ID, acquisition date, coverage, resolution,
              supported indicators, water methods, warnings, and
              quality information will appear here when catalogue data
              is available from the backend.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default DatasetsPage
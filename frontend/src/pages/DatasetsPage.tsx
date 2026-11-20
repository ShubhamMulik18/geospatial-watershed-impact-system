import { useEffect, useState } from 'react'

import DatasetUploader from '../components/datasets/DatasetUploader'
import DatasetValidationSummary, {
  type DatasetValidationData,
} from '../components/datasets/DatasetValidationSummary'
import { getDatasets } from '../services/datasetApi'
import type { DatasetMetadata } from '../types/dataset'

const pendingValidation: DatasetValidationData = {
  status: 'pending',
  warnings: [],
  errors: [],
  qualityInformation: null,
}

function DatasetsPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getDatasets()
      .then((data) => setDatasets(data))
      .catch(() => setDatasets([]))
      .finally(() => setIsLoading(false))
  }, [])

  function handleFileSelect(file: File) {
    setSelectedFile(file)
  }

  function handleFileRemove() {
    setSelectedFile(null)
  }

  const compatibleCount = datasets.filter((d) => d.isCompatible).length

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
          analysis. Catalogued satellite observations provide multi-temporal
          NDVI and surface water analysis.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Catalogue
          </p>

          <p className="mt-3 text-2xl font-bold text-white">
            {isLoading ? '...' : (datasets.length > 0 ? datasets.length : '0')}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {datasets.length > 0 ? 'Catalogued datasets' : 'Awaiting backend catalogue'}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Compatible
          </p>

          <p className="mt-3 text-2xl font-bold text-white">
            {isLoading ? '...' : (compatibleCount > 0 ? compatibleCount : '0')}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {compatibleCount > 0 ? 'Ready for watershed analysis' : 'No compatible datasets'}
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
              ? 'Local file selected'
              : 'No local dataset selected'}
          </p>
        </div>
      </section>

      {datasets.length > 0 && (
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="border-b border-slate-800 px-6 py-4">
            <h2 className="text-base font-semibold text-white">
              Catalogued Satellite Datasets
            </h2>
          </div>
          <div className="divide-y divide-slate-800">
            {datasets.map((d) => (
              <div key={d.id} className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
                <div>
                  <p className="font-medium text-slate-200">{d.displayName}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    ID: {d.id} · Acquisition: {d.acquisitionDate || 'N/A'} · Year: {d.year || 'N/A'}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
                    {d.resolution || '10m'}
                  </span>
                  <span className="rounded-full border border-sky-500/20 bg-sky-500/10 px-2.5 py-1 text-xs font-medium text-sky-300">
                    {d.supportedIndicators.join(', ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        <DatasetUploader
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
        />

        <DatasetValidationSummary
          validation={pendingValidation}
        />
      </div>
    </div>
  )
}

export default DatasetsPage

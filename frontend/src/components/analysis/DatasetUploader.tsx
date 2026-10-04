import { useRef, useState } from 'react'

import {
  uploadDataset,
  type DatasetUploadInput,
} from '../../services/datasetApi'
import type { DatasetMetadata } from '../../types/dataset'

type DatasetUploaderProps = {
  onUploadSuccess: (dataset: DatasetMetadata) => void
}

function parseCommaSeparatedValues(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function DatasetUploader({
  onUploadSuccess,
}: DatasetUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [acquisitionDate, setAcquisitionDate] =
    useState('')
  const [capabilities, setCapabilities] = useState('')
  const [waterMethods, setWaterMethods] = useState('')

  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] =
    useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] =
    useState<string | null>(null)

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const selectedFile = event.target.files?.[0] ?? null

    setUploadError(null)
    setUploadSuccess(null)

    if (!selectedFile) {
      setFile(null)
      return
    }

    const extension =
      selectedFile.name.split('.').pop()?.toLowerCase() ?? ''

    if (extension !== 'tif' && extension !== 'tiff') {
      setFile(null)

      setUploadError(
        'Only GeoTIFF files with .tif or .tiff extensions are supported.',
      )

      event.target.value = ''
      return
    }

    setFile(selectedFile)

    if (!displayName.trim()) {
      const nameWithoutExtension = selectedFile.name.replace(
        /\.(tif|tiff)$/i,
        '',
      )

      setDisplayName(nameWithoutExtension)
    }
  }

  function handleClear() {
    setFile(null)
    setDisplayName('')
    setAcquisitionDate('')
    setCapabilities('')
    setWaterMethods('')
    setUploadError(null)
    setUploadSuccess(null)

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setUploadError(null)
    setUploadSuccess(null)

    if (!file) {
      setUploadError('Select a GeoTIFF dataset to upload.')
      return
    }

    if (!displayName.trim()) {
      setUploadError('Enter a display name for the dataset.')
      return
    }

    if (!acquisitionDate) {
      setUploadError(
        'Select the acquisition date for the dataset.',
      )
      return
    }

    const uploadInput: DatasetUploadInput = {
      file,
      displayName: displayName.trim(),
      acquisitionDate,
      capabilities:
        parseCommaSeparatedValues(capabilities),
      waterMethods:
        parseCommaSeparatedValues(waterMethods),
    }

    setIsUploading(true)

    try {
      const uploadedDataset =
        await uploadDataset(uploadInput)

      setUploadSuccess(
        `${uploadedDataset.displayName} was uploaded successfully.`,
      )

      onUploadSuccess(uploadedDataset)

      setFile(null)
      setDisplayName('')
      setAcquisitionDate('')
      setCapabilities('')
      setWaterMethods('')

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      setUploadError(
        error instanceof Error
          ? error.message
          : 'Unable to upload the dataset.',
      )
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Dataset Upload
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Add GeoTIFF Dataset
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Upload a georeferenced TIFF dataset to the backend
          catalogue. The backend will inspect its spatial
          metadata before accepting it.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-6 p-6"
      >
        <div>
          <label
            htmlFor="dataset-file"
            className="text-sm font-medium text-slate-300"
          >
            GeoTIFF file
          </label>

          <div className="mt-2 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 p-5">
            <input
              ref={fileInputRef}
              id="dataset-file"
              type="file"
              accept=".tif,.tiff"
              disabled={isUploading}
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-400 file:mr-4 file:rounded-lg file:border-0 file:bg-emerald-500/10 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-emerald-300 hover:file:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            />

            <p className="mt-3 text-xs leading-5 text-slate-500">
              Accepted formats: .tif and .tiff. The backend
              validates the file, CRS, raster metadata and
              configured upload size limit.
            </p>

            {file && (
              <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3">
                <p className="text-sm font-medium text-slate-300">
                  {file.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label
              htmlFor="dataset-display-name"
              className="text-sm font-medium text-slate-300"
            >
              Display name
            </label>

            <input
              id="dataset-display-name"
              type="text"
              value={displayName}
              disabled={isUploading}
              onChange={(event) =>
                setDisplayName(event.target.value)
              }
              placeholder="Example: Watershed Survey 2025"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-emerald-500/60 disabled:cursor-not-allowed disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor="dataset-acquisition-date"
              className="text-sm font-medium text-slate-300"
            >
              Acquisition date
            </label>

            <input
              id="dataset-acquisition-date"
              type="date"
              value={acquisitionDate}
              disabled={isUploading}
              onChange={(event) =>
                setAcquisitionDate(event.target.value)
              }
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 outline-none transition focus:border-emerald-500/60 disabled:cursor-not-allowed disabled:opacity-60"
            />

            <p className="mt-2 text-xs text-slate-500">
              Required by the current backend dataset
              contract.
            </p>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label
              htmlFor="dataset-capabilities"
              className="text-sm font-medium text-slate-300"
            >
              Capabilities
              <span className="ml-2 text-xs font-normal text-slate-500">
                Optional
              </span>
            </label>

            <input
              id="dataset-capabilities"
              type="text"
              value={capabilities}
              disabled={isUploading}
              onChange={(event) =>
                setCapabilities(event.target.value)
              }
              placeholder="Comma-separated values"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-emerald-500/60 disabled:cursor-not-allowed disabled:opacity-60"
            />

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Leave empty if capabilities have not been
              established for this dataset.
            </p>
          </div>

          <div>
            <label
              htmlFor="dataset-water-methods"
              className="text-sm font-medium text-slate-300"
            >
              Water methods
              <span className="ml-2 text-xs font-normal text-slate-500">
                Optional
              </span>
            </label>

            <input
              id="dataset-water-methods"
              type="text"
              value={waterMethods}
              disabled={isUploading}
              onChange={(event) =>
                setWaterMethods(event.target.value)
              }
              placeholder="Comma-separated values"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-emerald-500/60 disabled:cursor-not-allowed disabled:opacity-60"
            />

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Leave empty when no water extraction method has
              been assigned.
            </p>
          </div>
        </div>

        {uploadError && (
          <div
            role="alert"
            className="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3"
          >
            <p className="text-sm font-medium text-rose-300">
              Upload failed
            </p>

            <p className="mt-1 text-sm leading-6 text-rose-300/80">
              {uploadError}
            </p>
          </div>
        )}

        {uploadSuccess && (
          <div
            role="status"
            className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3"
          >
            <p className="text-sm font-medium text-emerald-300">
              Upload complete
            </p>

            <p className="mt-1 text-sm leading-6 text-emerald-300/80">
              {uploadSuccess}
            </p>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3 border-t border-slate-800 pt-5">
          <button
            type="submit"
            disabled={isUploading}
            className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isUploading
              ? 'Uploading dataset...'
              : 'Upload dataset'}
          </button>

          <button
            type="button"
            disabled={isUploading}
            onClick={handleClear}
            className="rounded-xl border border-slate-700 px-5 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-600 hover:bg-slate-800/70 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Clear
          </button>

          <p className="text-xs text-slate-500">
            Uploads are sent to the real backend dataset
            catalogue.
          </p>
        </div>
      </form>
    </section>
  )
}

export default DatasetUploader
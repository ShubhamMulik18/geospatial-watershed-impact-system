import { useRef, useState } from 'react'

type DatasetUploaderProps = {
  onFileSelect?: (file: File) => void
  onFileRemove?: () => void
}

function DatasetUploader({
  onFileSelect,
  onFileRemove,
}: DatasetUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleFile(file: File | undefined) {
    if (!file) {
      return
    }

    setError(null)
    setSelectedFile(file)
    onFileSelect?.(file)
  }

  function handleInputChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    handleFile(event.target.files?.[0])
  }

  function handleDrop(
    event: React.DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault()

    const file = event.dataTransfer.files?.[0]

    if (!file) {
      setError('No dataset file was detected.')
      return
    }

    handleFile(file)
  }

  function handleDragOver(
    event: React.DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault()
  }

  function handleRemove() {
    setSelectedFile(null)
    setError(null)

    if (inputRef.current) {
      inputRef.current.value = ''
    }

    onFileRemove?.()
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Dataset Input
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Add Dataset
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Select a dataset file for catalogue validation. Backend
          upload and scientific validation will be connected when the
          dataset API is available.
        </p>
      </div>

      <div className="p-6">
        {!selectedFile ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/40 p-8 text-center transition hover:border-emerald-500/50 hover:bg-slate-950/70"
          >
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
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
                  d="M12 16V4m0 0-4 4m4-4 4 4M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"
                />
              </svg>
            </div>

            <p className="mt-4 font-medium text-slate-200">
              Drop a dataset file here
            </p>

            <p className="mt-1 text-sm text-slate-500">
              or select a file from your computer
            </p>

            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="mt-5 rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
            >
              Browse Dataset
            </button>

            <input
              ref={inputRef}
              type="file"
              onChange={handleInputChange}
              className="hidden"
            />

            <p className="mt-4 text-xs leading-5 text-slate-600">
              File-format and size restrictions will follow the
              backend dataset contract when available.
            </p>
          </div>
        ) : (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  Local file selected
                </p>

                <p className="mt-2 truncate font-medium text-slate-200">
                  {selectedFile.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>

              <button
                type="button"
                onClick={handleRemove}
                className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-red-500/40 hover:text-red-300"
              >
                Remove
              </button>
            </div>

            <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3">
              <p className="text-xs leading-5 text-amber-200/80">
                This file is selected locally only. It has not been
                uploaded or scientifically validated.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}
      </div>
    </section>
  )
}

export default DatasetUploader
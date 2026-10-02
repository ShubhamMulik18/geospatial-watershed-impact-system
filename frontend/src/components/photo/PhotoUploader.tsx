import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'

const MAX_FILE_SIZE = 10 * 1024 * 1024

const ACCEPTED_FILE_TYPES = ['image/jpeg', 'image/png']

type PhotoUploaderProps = {
  onFileSelect: (file: File) => void
}

function PhotoUploader({ onFileSelect }: PhotoUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  function validateFile(file: File) {
    if (!ACCEPTED_FILE_TYPES.includes(file.type)) {
      setError('Invalid file type. Please select a JPG or PNG image.')
      return false
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File is too large. Maximum allowed size is 10 MB.')
      return false
    }

    setError(null)
    return true
  }

  function processFile(file: File) {
    if (!validateFile(file)) {
      return
    }

    onFileSelect(file)
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    processFile(file)

    event.target.value = ''
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)

    const file = event.dataTransfer.files?.[0]

    if (!file) {
      return
    }

    processFile(file)
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function openFilePicker() {
    inputRef.current?.click()
  }

  return (
    <section
      aria-labelledby="photo-upload-title"
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Step 1
        </p>

        <h2
          id="photo-upload-title"
          className="mt-2 text-xl font-semibold text-white"
        >
          Upload Field Photo
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          Select a field photograph to begin the watershed analysis workflow.
        </p>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`mt-6 rounded-2xl border-2 border-dashed p-8 text-center transition ${
          isDragging
            ? 'border-emerald-400 bg-emerald-500/10'
            : 'border-slate-700 bg-slate-950/40 hover:border-slate-600'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-700 bg-slate-800 text-slate-300">
          <svg
            viewBox="0 0 24 24"
            className="h-7 w-7"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5"
            />

            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"
            />
          </svg>
        </div>

        <p className="mt-5 font-semibold text-slate-200">
          Drag and drop your field photo here
        </p>

        <p className="mt-2 text-sm text-slate-500">
          or select a file from your computer
        </p>

        <button
          type="button"
          onClick={openFilePicker}
          className="mt-5 rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
        >
          Choose Photo
        </button>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
          <span className="rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1">
            JPG
          </span>

          <span className="rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1">
            PNG
          </span>

          <span>Maximum 10 MB</span>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mt-4 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4"
        >
          <svg
            viewBox="0 0 24 24"
            className="mt-0.5 h-5 w-5 shrink-0 text-rose-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" />
            <path
              strokeLinecap="round"
              d="M12 8v5M12 16h.01"
            />
          </svg>

          <div>
            <p className="text-sm font-semibold text-rose-300">
              Photo could not be selected
            </p>

            <p className="mt-1 text-sm text-rose-300/80">
              {error}
            </p>
          </div>
        </div>
      )}

      <p className="mt-4 text-xs leading-5 text-slate-500">
        Your photo remains local at this stage. Backend upload will be connected
        during API integration.
      </p>
    </section>
  )
}

export default PhotoUploader
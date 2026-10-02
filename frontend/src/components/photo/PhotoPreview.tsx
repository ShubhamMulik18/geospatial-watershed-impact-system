type PhotoPreviewProps = {
  file: File
  previewUrl: string
  onRemove: () => void
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function PhotoPreview({
  file,
  previewUrl,
  onRemove,
}: PhotoPreviewProps) {
  return (
    <section
      aria-labelledby="photo-preview-title"
      className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70"
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Selected Photo
          </p>

          <h2
            id="photo-preview-title"
            className="mt-1 text-lg font-semibold text-white"
          >
            Photo Preview
          </h2>
        </div>

        <button
          type="button"
          onClick={onRemove}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-300 transition hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-300"
        >
          Remove
        </button>
      </div>

      <div className="p-6">
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
          <img
            src={previewUrl}
            alt={`Preview of ${file.name}`}
            className="h-72 w-full object-contain sm:h-96"
          />
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              File Name
            </p>

            <p
              className="mt-2 truncate text-sm font-medium text-slate-200"
              title={file.name}
            >
              {file.name}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              File Type
            </p>

            <p className="mt-2 text-sm font-medium text-slate-200">
              {file.type === 'image/png' ? 'PNG' : 'JPG'}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              File Size
            </p>

            <p className="mt-2 text-sm font-medium text-slate-200">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-start gap-3 rounded-xl border border-sky-500/20 bg-sky-500/10 p-4">
          <svg
            viewBox="0 0 24 24"
            className="mt-0.5 h-5 w-5 shrink-0 text-sky-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" />

            <path
              strokeLinecap="round"
              d="M12 11v5M12 8h.01"
            />
          </svg>

          <p className="text-sm leading-6 text-sky-200/80">
            This is a local browser preview. The photo has not been uploaded to
            the backend yet.
          </p>
        </div>
      </div>
    </section>
  )
}

export default PhotoPreview
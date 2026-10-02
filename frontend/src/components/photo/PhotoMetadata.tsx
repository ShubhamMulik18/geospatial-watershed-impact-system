type PhotoMetadataData = {
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  cameraMake: string | null
  cameraModel: string | null
}

type PhotoMetadataProps = {
  metadata: PhotoMetadataData
}

function MetadataValue({
  label,
  value,
}: {
  label: string
  value: string | number | null
}) {
  const isUnavailable = value === null

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </p>

      <p
        className={`mt-2 text-sm font-medium ${
          isUnavailable ? 'text-slate-500' : 'text-slate-200'
        }`}
      >
        {isUnavailable ? 'Unavailable' : value}
      </p>
    </div>
  )
}

function PhotoMetadata({ metadata }: PhotoMetadataProps) {
  const hasGps =
    metadata.latitude !== null && metadata.longitude !== null

  return (
    <section
      aria-labelledby="photo-metadata-title"
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Photo Information
          </p>

          <h2
            id="photo-metadata-title"
            className="mt-2 text-lg font-semibold text-white"
          >
            Photo Metadata
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-400">
            Metadata associated with the selected field photograph.
          </p>
        </div>

        <span
          className={`w-fit rounded-full border px-2.5 py-1 text-xs font-medium ${
            hasGps
              ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
              : 'border-amber-500/20 bg-amber-500/10 text-amber-300'
          }`}
        >
          {hasGps ? 'Location available' : 'Location unavailable'}
        </span>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <MetadataValue
          label="Latitude"
          value={metadata.latitude}
        />

        <MetadataValue
          label="Longitude"
          value={metadata.longitude}
        />

        <MetadataValue
          label="Capture Date"
          value={metadata.capturedAt}
        />

        <MetadataValue
          label="Camera Make"
          value={metadata.cameraMake}
        />

        <MetadataValue
          label="Camera Model"
          value={metadata.cameraModel}
        />
      </div>

      {!hasGps && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <svg
            viewBox="0 0 24 24"
            className="mt-0.5 h-5 w-5 shrink-0 text-amber-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"
            />

            <circle cx="12" cy="9" r="2.5" />
          </svg>

          <div>
            <p className="text-sm font-semibold text-amber-300">
              Photo location is unavailable
            </p>

            <p className="mt-1 text-sm leading-6 text-amber-200/70">
              GPS coordinates were not provided for this photo. The system will
              not estimate or invent a location.
            </p>
          </div>
        </div>
      )}

      {metadata.capturedAt === null && (
        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">
            Capture date is unavailable and will remain unset until valid
            metadata is provided.
          </p>
        </div>
      )}
    </section>
  )
}

export type { PhotoMetadataData }
export default PhotoMetadata
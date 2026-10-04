export type PhotoMetadataData = {
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  exifStatus: 'available' | 'partial' | 'missing' | 'invalid'
  warnings: string[]
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

function formatExifStatus(
  status: PhotoMetadataData['exifStatus'],
) {
  switch (status) {
    case 'available':
      return 'Available'
    case 'partial':
      return 'Partial'
    case 'missing':
      return 'Missing'
    case 'invalid':
      return 'Invalid'
  }
}

function PhotoMetadata({ metadata }: PhotoMetadataProps) {
  const hasGps =
    metadata.latitude !== null &&
    metadata.longitude !== null

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
            Metadata returned by the photo processing service.
          </p>
        </div>

        <span
          className={`w-fit rounded-full border px-2.5 py-1 text-xs font-medium ${
            hasGps
              ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
              : 'border-amber-500/20 bg-amber-500/10 text-amber-300'
          }`}
        >
          {hasGps
            ? 'Location available'
            : 'Location unavailable'}
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
          label="EXIF Status"
          value={formatExifStatus(metadata.exifStatus)}
        />
      </div>

      {metadata.warnings.length > 0 && (
        <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <p className="text-sm font-semibold text-amber-300">
            Metadata warnings
          </p>

          <ul className="mt-2 space-y-1 text-sm leading-6 text-amber-200/80">
            {metadata.warnings.map((warning, index) => (
              <li key={`${warning}-${index}`}>
                • {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!hasGps && (
        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">
            GPS coordinates are unavailable. The frontend will
            not estimate or invent a photo location.
          </p>
        </div>
      )}

      {metadata.capturedAt === null && (
        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">
            Capture date is unavailable and will remain unset.
          </p>
        </div>
      )}
    </section>
  )
}

export default PhotoMetadata

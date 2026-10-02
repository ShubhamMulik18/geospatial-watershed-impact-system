import type { PolygonValidationResult } from '../../utils/polygonValidation'

type StudyAreaStatusProps = {
  hasStudyArea: boolean
  vertexCount: number
  validation: PolygonValidationResult | null
  isConfirmed: boolean
  onConfirm: () => void
}

function StudyAreaStatus({
  hasStudyArea,
  vertexCount,
  validation,
  isConfirmed,
  onConfirm,
}: StudyAreaStatusProps) {
  const isValid =
    hasStudyArea && validation?.isValid === true

  return (
    <div className="border-t border-slate-800 bg-slate-950/40 px-6 py-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          {!hasStudyArea && (
            <>
              <p className="text-sm font-medium text-slate-300">
                No study area polygon drawn
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                Use the polygon tool on the map to define the study
                area.
              </p>
            </>
          )}

          {hasStudyArea && !isValid && validation && (
            <>
              <p className="text-sm font-medium text-red-300">
                Study area polygon is invalid
              </p>

              <div className="mt-2 space-y-1">
                {validation.errors.map((error) => (
                  <p
                    key={error}
                    className="text-xs leading-5 text-red-300/80"
                  >
                    {error}
                  </p>
                ))}
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Edit the polygon until the geometry is valid before
                confirming the study area.
              </p>
            </>
          )}

          {hasStudyArea && isValid && !isConfirmed && (
            <>
              <p className="text-sm font-medium text-emerald-300">
                Study area polygon is valid
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                {vertexCount} polygon vertices captured in GeoJSON
                coordinate order.
              </p>

              <p className="mt-1 text-xs leading-5 text-amber-300/80">
                Confirmation is required before continuing with this
                study area.
              </p>
            </>
          )}

          {hasStudyArea && isValid && isConfirmed && (
            <>
              <div className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-xs text-emerald-300">
                  ✓
                </span>

                <p className="text-sm font-medium text-emerald-300">
                  Study area confirmed
                </p>
              </div>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                {vertexCount} polygon vertices are currently confirmed.
                Editing or deleting the polygon will require
                confirmation again.
              </p>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={onConfirm}
          disabled={!isValid || isConfirmed}
          className="inline-flex min-h-10 items-center justify-center rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
        >
          {isConfirmed
            ? 'Study Area Confirmed'
            : 'Confirm Study Area'}
        </button>
      </div>
    </div>
  )
}

export default StudyAreaStatus
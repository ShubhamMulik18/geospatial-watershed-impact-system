export type DatasetValidationStatus =
  | 'pending'
  | 'valid'
  | 'invalid'

export type DatasetValidationData = {
  status: DatasetValidationStatus
  warnings: string[]
  errors: string[]
  qualityInformation: string | null
}

type DatasetValidationSummaryProps = {
  validation: DatasetValidationData
}

function DatasetValidationSummary({
  validation,
}: DatasetValidationSummaryProps) {
  const isPending = validation.status === 'pending'
  const isValid = validation.status === 'valid'
  const isInvalid = validation.status === 'invalid'

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Dataset Validation
            </p>

            <h2 className="mt-1 text-lg font-semibold text-white">
              Validation Summary
            </h2>
          </div>

          {isPending && (
            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
              Pending
            </span>
          )}

          {isValid && (
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
              Valid
            </span>
          )}

          {isInvalid && (
            <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs font-medium text-red-300">
              Invalid
            </span>
          )}
        </div>
      </div>

      <div className="space-y-5 p-6">
        {isPending && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
            <p className="text-sm font-medium text-amber-200">
              Validation has not been completed
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-400">
              Dataset compatibility, metadata, and quality checks will
              be provided by the backend validation workflow.
            </p>
          </div>
        )}

        {isValid && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <p className="text-sm font-medium text-emerald-300">
              Dataset passed validation
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-400">
              No blocking validation errors were reported.
            </p>
          </div>
        )}

        {isInvalid && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
            <p className="text-sm font-medium text-red-300">
              Dataset failed validation
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-400">
              Resolve the reported validation errors before using this
              dataset for analysis.
            </p>
          </div>
        )}

        {validation.errors.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-red-300">
              Errors
            </p>

            <div className="mt-2 space-y-2">
              {validation.errors.map((error) => (
                <div
                  key={error}
                  className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3"
                >
                  <p className="text-sm text-red-200">
                    {error}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {validation.warnings.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-300">
              Warnings
            </p>

            <div className="mt-2 space-y-2">
              {validation.warnings.map((warning) => (
                <div
                  key={warning}
                  className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3"
                >
                  <p className="text-sm text-amber-200">
                    {warning}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Quality Information
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-300">
            {validation.qualityInformation ?? 'Unavailable'}
          </p>
        </div>
      </div>
    </section>
  )
}

export default DatasetValidationSummary
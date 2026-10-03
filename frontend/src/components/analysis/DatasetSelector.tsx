import type { DatasetMetadata } from '../../types/dataset'

type DatasetSelectorProps = {
  datasets: DatasetMetadata[]
  selectedDatasetIds: string[]
  onSelectionChange: (datasetIds: string[]) => void
}

function DatasetSelector({
  datasets,
  selectedDatasetIds,
  onSelectionChange,
}: DatasetSelectorProps) {
  function handleToggle(dataset: DatasetMetadata) {
    if (!dataset.isCompatible) {
      return
    }

    const isSelected = selectedDatasetIds.includes(dataset.id)

    if (isSelected) {
      onSelectionChange(
        selectedDatasetIds.filter(
          (datasetId) => datasetId !== dataset.id,
        ),
      )
      return
    }

    onSelectionChange([
      ...selectedDatasetIds,
      dataset.id,
    ])
  }

  const selectedCount = selectedDatasetIds.length
  const minimumReached = selectedCount >= 2

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Dataset Selection
            </p>

            <h2 className="mt-1 text-lg font-semibold text-white">
              Select Comparison Datasets
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Choose at least two distinct compatible datasets for
              watershed comparison.
            </p>
          </div>

          <div
            className={`rounded-full border px-3 py-1 text-xs font-medium ${
              minimumReached
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
            }`}
          >
            {selectedCount} selected
          </div>
        </div>
      </div>

      <div className="p-6">
        {datasets.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-8 text-center">
            <p className="font-medium text-slate-300">
              No datasets available
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Compatible datasets will appear here when they are
              available from the dataset catalogue.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {datasets.map((dataset) => {
              const isSelected =
                selectedDatasetIds.includes(dataset.id)

              return (
                <button
                  key={dataset.id}
                  type="button"
                  disabled={!dataset.isCompatible}
                  onClick={() => handleToggle(dataset)}
                  className={`rounded-xl border p-5 text-left transition ${
                    !dataset.isCompatible
                      ? 'cursor-not-allowed border-slate-800 bg-slate-950/30 opacity-60'
                      : isSelected
                        ? 'border-emerald-500/50 bg-emerald-500/10'
                        : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-950/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-200">
                        {dataset.displayName}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        ID: {dataset.id}
                      </p>
                    </div>

                    {dataset.isCompatible ? (
                      <span
                        className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${
                          isSelected
                            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                            : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        {isSelected ? 'Selected' : 'Available'}
                      </span>
                    ) : (
                      <span className="shrink-0 rounded-full border border-red-500/20 bg-red-500/5 px-2.5 py-1 text-xs font-medium text-red-300">
                        Incompatible
                      </span>
                    )}
                  </div>

                  <div className="mt-5 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-600">
                        Year
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {dataset.year ?? 'Unavailable'}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-600">
                        Resolution
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {dataset.resolution ?? 'Unavailable'}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-600">
                        Acquisition
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {dataset.acquisitionDate ?? 'Unavailable'}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-600">
                        Coverage
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {dataset.coverage ?? 'Unavailable'}
                      </p>
                    </div>
                  </div>

                  {!dataset.isCompatible &&
                    dataset.incompatibilityReason && (
                      <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2">
                        <p className="text-xs leading-5 text-red-200">
                          {dataset.incompatibilityReason}
                        </p>
                      </div>
                    )}

                  {dataset.warnings.length > 0 && (
                    <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
                      <p className="text-xs text-amber-200">
                        {dataset.warnings.length}{' '}
                        {dataset.warnings.length === 1
                          ? 'warning'
                          : 'warnings'}{' '}
                        reported
                      </p>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        )}

        <div
          className={`mt-5 rounded-xl border px-4 py-3 ${
            minimumReached
              ? 'border-emerald-500/20 bg-emerald-500/5'
              : 'border-amber-500/20 bg-amber-500/5'
          }`}
        >
          <p
            className={`text-sm ${
              minimumReached
                ? 'text-emerald-300'
                : 'text-amber-200'
            }`}
          >
            {minimumReached
              ? 'Minimum dataset requirement satisfied.'
              : `Select at least ${2 - selectedCount} more compatible ${
                  2 - selectedCount === 1 ? 'dataset' : 'datasets'
                }.`}
          </p>
        </div>
      </div>
    </section>
  )
}

export default DatasetSelector
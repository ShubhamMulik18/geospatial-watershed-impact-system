export type IndicatorOption = {
  id: string
  displayName: string
  description: string | null
  isSupported: boolean
  unsupportedReason: string | null
}

type IndicatorSelectorProps = {
  indicators: IndicatorOption[]
  selectedIndicatorIds: string[]
  onSelectionChange: (indicatorIds: string[]) => void
}

function IndicatorSelector({
  indicators,
  selectedIndicatorIds,
  onSelectionChange,
}: IndicatorSelectorProps) {
  function handleToggle(indicator: IndicatorOption) {
    if (!indicator.isSupported) {
      return
    }

    const isSelected = selectedIndicatorIds.includes(indicator.id)

    if (isSelected) {
      onSelectionChange(
        selectedIndicatorIds.filter(
          (indicatorId) => indicatorId !== indicator.id,
        ),
      )
      return
    }

    onSelectionChange([
      ...selectedIndicatorIds,
      indicator.id,
    ])
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Analysis Indicators
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Select Indicators
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Choose the indicators to include in the watershed analysis.
          Availability depends on the selected datasets and backend
          compatibility checks.
        </p>
      </div>

      <div className="p-6">
        {indicators.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-8 text-center">
            <p className="font-medium text-slate-300">
              No indicators available
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Indicator options will appear after compatible datasets
              are available.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {indicators.map((indicator) => {
              const isSelected =
                selectedIndicatorIds.includes(indicator.id)

              return (
                <button
                  key={indicator.id}
                  type="button"
                  disabled={!indicator.isSupported}
                  onClick={() => handleToggle(indicator)}
                  className={`rounded-xl border p-5 text-left transition ${
                    !indicator.isSupported
                      ? 'cursor-not-allowed border-slate-800 bg-slate-950/30 opacity-60'
                      : isSelected
                        ? 'border-emerald-500/50 bg-emerald-500/10'
                        : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-950/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-200">
                        {indicator.displayName}
                      </p>

                      {indicator.description && (
                        <p className="mt-2 text-sm leading-6 text-slate-500">
                          {indicator.description}
                        </p>
                      )}
                    </div>

                    {indicator.isSupported ? (
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
                        Unsupported
                      </span>
                    )}
                  </div>

                  {!indicator.isSupported && (
                    <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2">
                      <p className="text-xs leading-5 text-red-200">
                        {indicator.unsupportedReason ??
                          'This indicator is unavailable for the current dataset selection.'}
                      </p>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        )}

        <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/30 px-4 py-3">
          <p className="text-sm text-slate-400">
            {selectedIndicatorIds.length === 0
              ? 'No indicators selected.'
              : `${selectedIndicatorIds.length} ${
                  selectedIndicatorIds.length === 1
                    ? 'indicator'
                    : 'indicators'
                } selected.`}
          </p>
        </div>
      </div>
    </section>
  )
}

export default IndicatorSelector
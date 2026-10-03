export type AnalysisMode =
  | 'before-after'
  | 'multi-date'

export type AnalysisModeOption = {
  id: AnalysisMode
  displayName: string
  description: string
  isAvailable: boolean
  unavailableReason: string | null
}

type AnalysisControlsProps = {
  modes: AnalysisModeOption[]
  selectedMode: AnalysisMode | null
  onModeChange: (mode: AnalysisMode) => void
}

function AnalysisControls({
  modes,
  selectedMode,
  onModeChange,
}: AnalysisControlsProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Analysis Configuration
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Comparison Mode
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Select how the available datasets should be compared.
          Supported modes depend on the dataset configuration returned
          by the analysis workflow.
        </p>
      </div>

      <div className="p-6">
        {modes.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-8 text-center">
            <p className="font-medium text-slate-300">
              No comparison modes available
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Comparison options will appear after compatible datasets
              are selected.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {modes.map((mode) => {
              const isSelected = selectedMode === mode.id

              return (
                <button
                  key={mode.id}
                  type="button"
                  disabled={!mode.isAvailable}
                  onClick={() => onModeChange(mode.id)}
                  className={`rounded-xl border p-5 text-left transition ${
                    !mode.isAvailable
                      ? 'cursor-not-allowed border-slate-800 bg-slate-950/30 opacity-60'
                      : isSelected
                        ? 'border-emerald-500/50 bg-emerald-500/10'
                        : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-950/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-200">
                        {mode.displayName}
                      </p>

                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        {mode.description}
                      </p>
                    </div>

                    {mode.isAvailable ? (
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
                      <span className="shrink-0 rounded-full border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-500">
                        Unavailable
                      </span>
                    )}
                  </div>

                  {!mode.isAvailable && (
                    <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
                      <p className="text-xs leading-5 text-amber-200">
                        {mode.unavailableReason ??
                          'This comparison mode is not available for the current dataset selection.'}
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
            {selectedMode
              ? 'Comparison mode selected.'
              : 'Select an available comparison mode to continue.'}
          </p>
        </div>
      </div>
    </section>
  )
}

export default AnalysisControls
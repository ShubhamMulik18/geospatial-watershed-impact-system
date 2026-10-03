type ReportDownloadProps = {
  available?: boolean
  onDownload?: () => void
}

function ReportDownload({
  available = false,
  onDownload,
}: ReportDownloadProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Analysis Report
          </p>

          <h2 className="mt-1 text-xl font-semibold text-white">
            Download Report
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            A downloadable analysis report will be available when report
            generation is connected in the dedicated reporting phase.
          </p>
        </div>

        <button
          type="button"
          disabled={!available}
          onClick={available ? onDownload : undefined}
          className={`inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl px-5 py-3 text-sm font-semibold transition ${
            available
              ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
              : 'cursor-not-allowed border border-slate-700 bg-slate-800 text-slate-500'
          }`}
        >
          {available ? 'Download Report' : 'Report Unavailable'}
        </button>
      </div>

      {!available && (
        <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3">
          <p className="text-xs leading-5 text-slate-500">
            Report generation is not connected in the current mock
            workflow.
          </p>
        </div>
      )}
    </section>
  )
}

export default ReportDownload
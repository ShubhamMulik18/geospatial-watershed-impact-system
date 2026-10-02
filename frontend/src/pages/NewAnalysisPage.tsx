function NewAnalysisPage() {
  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
        Analysis Workspace
      </p>

      <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
        New Analysis
      </h1>

      <p className="mt-3 max-w-2xl leading-7 text-slate-400">
        Create a new watershed impact analysis using field photos, a confirmed
        study area, satellite datasets, and selected indicators.
      </p>

      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm text-slate-500">Analysis workflow</p>
        <p className="mt-2 font-medium text-slate-300">
          Photo upload, prediction, Web GIS, and analysis controls will be
          implemented in their dedicated phases.
        </p>
      </div>
    </section>
  )
}

export default NewAnalysisPage
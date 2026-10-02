function DatasetsPage() {
  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
        Data Catalogue
      </p>

      <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
        Datasets
      </h1>

      <p className="mt-3 max-w-2xl leading-7 text-slate-400">
        Browse and manage satellite datasets available for watershed impact
        analysis.
      </p>

      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm text-slate-500">Dataset catalogue</p>

        <p className="mt-2 font-medium text-slate-300">
          Dataset metadata, validation, and selection controls will be
          implemented in the dataset phase.
        </p>
      </div>
    </section>
  )
}

export default DatasetsPage
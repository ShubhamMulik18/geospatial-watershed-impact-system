function DashboardPage() {
  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-400">
        Overview
      </p>

      <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
        Dashboard
      </h1>

      <p className="mt-3 max-w-2xl leading-7 text-slate-400">
        Monitor watershed analyses, review recent activity, and start a new
        geospatial impact assessment.
      </p>

      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm text-slate-500">Dashboard content</p>
        <p className="mt-2 font-medium text-slate-300">
          Summary cards and recent analyses will be added in Phase 4.
        </p>
      </div>
    </section>
  )
}

export default DashboardPage
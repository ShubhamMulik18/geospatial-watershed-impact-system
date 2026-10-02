function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
      <section className="w-full max-w-3xl rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center shadow-2xl">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500 text-3xl font-bold text-white shadow-lg">
          W
        </div>

        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Frontend Foundation
        </p>

        <h1 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
          Geospatial Watershed
          <span className="block text-emerald-400">
            Impact Analysis System
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-slate-400">
          React, TypeScript, Vite and Tailwind CSS are ready for the Web GIS
          frontend.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <span className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200">
            React
          </span>

          <span className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200">
            TypeScript
          </span>

          <span className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200">
            Vite
          </span>

          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-400">
            Tailwind CSS
          </span>
        </div>
      </section>
    </main>
  )
}

export default App
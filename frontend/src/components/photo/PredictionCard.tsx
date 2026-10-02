function PredictionCard() {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        AI Prediction
      </p>

      <h2 className="mt-2 text-lg font-semibold text-white">
        Prediction Pending
      </h2>

      <p className="mt-2 text-sm leading-6 text-slate-400">
        AI prediction will become available after the photo upload and
        prediction services are connected.
      </p>

      <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <p className="text-sm text-slate-500">
          No prediction has been generated.
        </p>
      </div>
    </section>
  )
}

export default PredictionCard
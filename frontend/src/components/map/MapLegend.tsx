type MapLegendProps = {
  hasLocation: boolean
}

function MapLegend({ hasLocation }: MapLegendProps) {
  return (
    <div className="absolute bottom-8 left-3 z-[400] min-w-40 rounded-xl border border-slate-700/80 bg-slate-950/90 p-3 shadow-xl backdrop-blur-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-300">
        Map Legend
      </p>

      <div className="mt-3 space-y-2">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-sm border border-slate-400 bg-slate-200" />

          <span className="text-xs text-slate-300">
            OpenStreetMap
          </span>
        </div>

        {hasLocation && (
          <div className="flex items-center gap-2">
            <span className="flex h-3 w-3 items-center justify-center rounded-full bg-emerald-500">
              <span className="h-1.5 w-1.5 rounded-full bg-white" />
            </span>

            <span className="text-xs text-slate-300">
              Field photo location
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default MapLegend
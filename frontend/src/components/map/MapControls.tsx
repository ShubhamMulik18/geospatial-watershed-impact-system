import { useEffect } from 'react'
import { useMap } from 'react-leaflet'

type MapControlsProps = {
  center: [number, number]
  zoom: number
}

function MapControls({ center, zoom }: MapControlsProps) {
  const map = useMap()

  useEffect(() => {
    const container = map.getContainer()

    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize()
    })

    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
    }
  }, [map])

  function handleResetView() {
    map.setView(center, zoom)
  }

  return (
    <div className="leaflet-top leaflet-right">
      <div className="leaflet-control">
        <button
          type="button"
          onClick={handleResetView}
          className="rounded-lg border border-slate-700 bg-slate-950/90 px-3 py-2 text-xs font-semibold text-slate-200 shadow-lg transition hover:border-emerald-500/40 hover:bg-slate-900 hover:text-emerald-300"
          title="Reset map view"
        >
          Reset view
        </button>
      </div>
    </div>
  )
}

export default MapControls
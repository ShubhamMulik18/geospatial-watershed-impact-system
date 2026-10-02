import { MapContainer, TileLayer } from 'react-leaflet'

import type { GeoJsonPosition } from '../../utils/coordinates'
import { geoJsonToLeaflet } from '../../utils/coordinates'
import InterventionMarker from './InterventionMarker'
import MapControls from './MapControls'
import MapLegend from './MapLegend'

type AnalysisMapProps = {
  location?: GeoJsonPosition | null
}

const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629]

function AnalysisMap({ location = null }: AnalysisMapProps) {
  const markerPosition = location ? geoJsonToLeaflet(location) : null
  const mapCenter = markerPosition ?? DEFAULT_CENTER
  const mapZoom = location ? 15 : 5

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="flex flex-col gap-2 border-b border-slate-800 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
            Web GIS
          </p>

          <h2 className="mt-1 text-lg font-semibold text-white">
            Study Area Map
          </h2>
        </div>

        <div className="text-sm text-slate-400">
          {location ? 'Location available' : 'Location unavailable'}
        </div>
      </div>

      <div className="relative h-[520px] w-full">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapControls
            center={mapCenter}
            zoom={mapZoom}
          />

          <MapLegend hasLocation={Boolean(location)} />

          {location && (
            <InterventionMarker
              location={location}
              label="Field photo location"
            />
          )}
        </MapContainer>
      </div>

      <div className="border-t border-slate-800 bg-slate-950/40 px-6 py-4">
        {location ? (
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <p className="text-slate-400">
              Latitude:{' '}
              <span className="font-medium text-slate-200">
                {location[1].toFixed(6)}
              </span>
            </p>

            <p className="text-slate-400">
              Longitude:{' '}
              <span className="font-medium text-slate-200">
                {location[0].toFixed(6)}
              </span>
            </p>
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No verified location is available. A map marker will only be shown
            when valid coordinates are provided.
          </p>
        )}
      </div>
    </section>
  )
}

export default AnalysisMap
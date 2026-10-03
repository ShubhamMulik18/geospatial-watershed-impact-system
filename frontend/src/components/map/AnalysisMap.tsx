import { useCallback } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'

import { useAnalysis } from '../../context/useAnalysis'
import type { GeoJsonPosition } from '../../utils/coordinates'
import { geoJsonToLeaflet } from '../../utils/coordinates'
import { validatePolygonRing } from '../../utils/polygonValidation'
import InterventionMarker from './InterventionMarker'
import MapControls from './MapControls'
import MapLegend from './MapLegend'
import PolygonEditor, {
  type StudyAreaPolygon,
} from './PolygonEditor'
import StudyAreaStatus from './StudyAreaStatus'

type AnalysisMapProps = {
  location?: GeoJsonPosition | null
}

const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629]

function AnalysisMap({ location = null }: AnalysisMapProps) {
  const {
    draftPolygon,
    confirmedPolygon,
    setDraftPolygon,
    confirmPolygon,
  } = useAnalysis()

  const markerPosition = location
    ? geoJsonToLeaflet(location)
    : null

  const mapCenter = markerPosition ?? DEFAULT_CENTER
  const mapZoom = location ? 15 : 5

  const handlePolygonChange = useCallback(
    (polygon: StudyAreaPolygon | null) => {
      setDraftPolygon(polygon)
    },
    [setDraftPolygon],
  )

  const vertexCount = draftPolygon
    ? Math.max(
        draftPolygon.coordinates[0].length - 1,
        0,
      )
    : 0

  const validation = draftPolygon
    ? validatePolygonRing(
        draftPolygon.coordinates[0],
      )
    : null

  const isStudyAreaValid =
    draftPolygon !== null &&
    validation?.isValid === true

  const isStudyAreaConfirmed =
    draftPolygon !== null &&
    confirmedPolygon !== null

  function handleConfirmStudyArea() {
    if (!draftPolygon || !isStudyAreaValid) {
      return
    }

    confirmPolygon(draftPolygon)
  }

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

        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className="text-slate-400">
            {location
              ? 'Location available'
              : 'Location unavailable'}
          </span>

          {draftPolygon && !isStudyAreaValid && (
            <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs font-medium text-red-300">
              Invalid study area
            </span>
          )}

          {draftPolygon &&
            isStudyAreaValid &&
            !isStudyAreaConfirmed && (
              <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
                Awaiting confirmation
              </span>
            )}

          {draftPolygon &&
            isStudyAreaValid &&
            isStudyAreaConfirmed && (
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                Study area confirmed
              </span>
            )}
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

          <MapLegend
            hasLocation={Boolean(location)}
          />

          <PolygonEditor
            polygon={draftPolygon}
            onPolygonChange={handlePolygonChange}
          />

          {location && (
            <InterventionMarker
              location={location}
              label="Field photo location"
            />
          )}
        </MapContainer>
      </div>

      <StudyAreaStatus
        hasStudyArea={draftPolygon !== null}
        vertexCount={vertexCount}
        validation={validation}
        isConfirmed={isStudyAreaConfirmed}
        onConfirm={handleConfirmStudyArea}
      />

      {location && (
        <div className="border-t border-slate-800 bg-slate-950/60 px-6 py-3">
          <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs">
            <p className="text-slate-500">
              Latitude:{' '}
              <span className="font-medium text-slate-300">
                {location[1].toFixed(6)}
              </span>
            </p>

            <p className="text-slate-500">
              Longitude:{' '}
              <span className="font-medium text-slate-300">
                {location[0].toFixed(6)}
              </span>
            </p>
          </div>
        </div>
      )}
    </section>
  )
}

export default AnalysisMap
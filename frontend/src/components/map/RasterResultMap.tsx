import { useEffect, useMemo, useState } from 'react'
import {
  MapContainer,
  TileLayer,
  useMap,
} from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

import type { RasterResultLayer } from '../../types/analysisResult'
import RasterOverlay from './RasterOverlay'

type RasterResultMapProps = {
  layers: RasterResultLayer[]
}

type FitRasterBoundsProps = {
  boundsWgs84: [number, number, number, number]
}

function FitRasterBounds({
  boundsWgs84,
}: FitRasterBoundsProps) {
  const map = useMap()

  useEffect(() => {
    const [left, bottom, right, top] = boundsWgs84

    const bounds: LatLngBoundsExpression = [
      [bottom, left],
      [top, right],
    ]

    map.fitBounds(bounds, {
      padding: [24, 24],
    })
  }, [boundsWgs84, map])

  return null
}

function isSupportedPreviewCrs(previewCrs: string) {
  const normalizedCrs = previewCrs
    .trim()
    .toUpperCase()

  return (
    normalizedCrs === 'EPSG:4326' ||
    normalizedCrs === 'WGS84' ||
    normalizedCrs === 'WGS 84'
  )
}

function hasValidBounds(
  bounds: [number, number, number, number],
) {
  const [left, bottom, right, top] = bounds

  return (
    Number.isFinite(left) &&
    Number.isFinite(bottom) &&
    Number.isFinite(right) &&
    Number.isFinite(top) &&
    left < right &&
    bottom < top &&
    left >= -180 &&
    right <= 180 &&
    bottom >= -90 &&
    top <= 90
  )
}

function formatLegendValue(value: unknown) {
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value)
  }

  return null
}

function RasterResultMap({
  layers,
}: RasterResultMapProps) {
  const displayableLayers = useMemo(
    () =>
      layers.filter(
        (layer) =>
          layer.preview_url !== null &&
          isSupportedPreviewCrs(layer.preview_crs) &&
          hasValidBounds(layer.bounds_wgs84),
      ),
    [layers],
  )

  const [selectedLayerId, setSelectedLayerId] =
    useState<string | null>(null)

  const [visible, setVisible] = useState(true)
  const [opacity, setOpacity] = useState(0.7)

  const selectedLayer =
    displayableLayers.find(
      (layer) => layer.layer_id === selectedLayerId,
    ) ??
    displayableLayers[0] ??
    null

  if (layers.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Raster Result Layers
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Result Layers Unavailable
        </h2>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
          No raster result layers are available for this analysis yet.
          The frontend will display backend generated map layers here
          when they are returned.
        </p>
      </section>
    )
  }

  if (
    displayableLayers.length === 0 ||
    selectedLayer === null
  ) {
    return (
      <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-300">
          Raster Result Layers
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          No Displayable Preview
        </h2>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
          Raster layer metadata was returned, but no layer currently
          has a supported WGS84 preview, valid geographic bounds, and
          a preview URL that can be safely placed on this Leaflet map.
        </p>
      </section>
    )
  }

  const legendEntries = Object.entries(
    selectedLayer.legend,
  )

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 p-6">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
              Raster Result Layers
            </p>

            <h2 className="mt-1 text-xl font-semibold text-white">
              Geospatial Result Map
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Preview layers are positioned using geographic bounds
              supplied by the backend. The frontend does not infer
              spatial bounds from image pixels.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Layer
              </span>

              <select
                value={selectedLayer.layer_id}
                onChange={(event) => {
                  setSelectedLayerId(event.target.value)
                  setVisible(true)
                }}
                className="mt-2 min-h-11 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 text-sm text-slate-200 outline-none transition focus:border-emerald-500"
              >
                {displayableLayers.map((layer) => (
                  <option
                    key={layer.layer_id}
                    value={layer.layer_id}
                  >
                    {layer.kind}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Visibility
              </span>

              <div className="mt-2 flex min-h-11 items-center rounded-xl border border-slate-700 bg-slate-950 px-3">
                <input
                  type="checkbox"
                  checked={visible}
                  onChange={(event) =>
                    setVisible(event.target.checked)
                  }
                  className="h-4 w-4 accent-emerald-500"
                />

                <span className="ml-2 text-sm text-slate-300">
                  Show layer
                </span>
              </div>
            </label>

            <label className="block">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Opacity {Math.round(opacity * 100)}%
              </span>

              <div className="mt-2 flex min-h-11 items-center rounded-xl border border-slate-700 bg-slate-950 px-3">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={opacity}
                  onChange={(event) =>
                    setOpacity(Number(event.target.value))
                  }
                  className="w-full accent-emerald-500"
                />
              </div>
            </label>
          </div>
        </div>
      </div>

      <div className="relative h-[480px]">
        <MapContainer
          center={[20.5937, 78.9629]}
          zoom={5}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitRasterBounds
            boundsWgs84={selectedLayer.bounds_wgs84}
          />

          <RasterOverlay
            layer={selectedLayer}
            opacity={opacity}
            visible={visible}
          />
        </MapContainer>

        {legendEntries.length > 0 && (
          <div className="absolute bottom-4 right-4 z-[500] max-h-52 min-w-44 overflow-auto rounded-xl border border-slate-700 bg-slate-950/95 p-4 shadow-xl backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Legend
            </p>

            <div className="mt-3 space-y-2">
              {legendEntries.map(
                ([label, value]) => {
                  const displayValue =
                    formatLegendValue(value)

                  if (displayValue === null) {
                    return null
                  }

                  return (
                    <div
                      key={label}
                      className="flex items-center justify-between gap-4 text-xs"
                    >
                      <span className="text-slate-400">
                        {label}
                      </span>

                      <span className="font-medium text-slate-200">
                        {displayValue}
                      </span>
                    </div>
                  )
                },
              )}
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-4 border-t border-slate-800 p-5 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            Kind
          </p>

          <p className="mt-1 text-sm font-medium text-slate-200">
            {selectedLayer.kind}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            Preview CRS
          </p>

          <p className="mt-1 font-mono text-sm text-slate-200">
            {selectedLayer.preview_crs}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            Dataset
          </p>

          <p className="mt-1 break-all font-mono text-sm text-slate-200">
            {selectedLayer.dataset_id}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            Raster File
          </p>

          {selectedLayer.download_url ? (
            <a
              href={selectedLayer.download_url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block text-sm font-semibold text-emerald-400 transition hover:text-emerald-300"
            >
              Download result
            </a>
          ) : (
            <p className="mt-1 text-sm text-slate-400">
              Unavailable
            </p>
          )}
        </div>
      </div>

      <div className="border-t border-slate-800 bg-slate-950/30 px-5 py-4">
        <p className="text-xs leading-5 text-slate-500">
          NoData handling belongs to the geospatial processing
          pipeline. This frontend visualizes the preview and spatial
          metadata returned by the backend and does not independently
          alter scientific raster values.
        </p>
      </div>
    </section>
  )
}

export default RasterResultMap
import { useEffect, useMemo, useState } from 'react'
import {
  MapContainer,
  TileLayer,
  useMap,
} from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

import type { DatasetResult, RasterResultLayer } from '../../types/analysisResult'
import RasterOverlay from './RasterOverlay'

type RasterResultMapProps = {
  layers: RasterResultLayer[]
  datasetResults?: DatasetResult[]
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
      padding: [20, 20],
      maxZoom: 16,
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
    normalizedCrs === 'WGS 84' ||
    normalizedCrs === 'EPSG:3857' ||
    normalizedCrs === 'EPSG:32643'
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

type SingleMapPanelProps = {
  title: string
  subtitle: string
  tag: string
  tagColor: 'blue' | 'emerald' | 'amber'
  layer: RasterResultLayer | null
  opacity: number
  visible: boolean
  metricInfo?: string | null
}

function SingleMapPanel({
  title,
  subtitle,
  tag,
  tagColor,
  layer,
  opacity,
  visible,
  metricInfo,
}: SingleMapPanelProps) {
  if (!layer || !layer.preview_url) {
    return (
      <div className="flex min-h-[460px] flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-950/40 p-8 text-center">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {tag}
        </p>
        <h4 className="mt-2 text-base font-semibold text-white">{title}</h4>
        <p className="mt-2 text-sm text-slate-400">
          No displayable raster layer available for this observation.
        </p>
      </div>
    )
  }

  const badgeStyle =
    tagColor === 'blue'
      ? 'border-sky-500/30 bg-sky-500/10 text-sky-300'
      : tagColor === 'emerald'
        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
        : 'border-amber-500/30 bg-amber-500/10 text-amber-300'

  const legendEntries = Object.entries(layer.legend || {})

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60 shadow-lg">
      <div className="flex flex-col justify-between gap-2 border-b border-slate-800/80 bg-slate-900/60 px-5 py-3.5 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide uppercase ${badgeStyle}`}
            >
              {tag}
            </span>
            <span className="text-sm font-semibold text-white">{title}</span>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
        </div>

        {metricInfo && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1 text-right">
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Observation Metric
            </p>
            <p className="font-mono text-sm font-semibold text-emerald-400">
              {metricInfo}
            </p>
          </div>
        )}
      </div>

      <div className="relative h-[420px] w-full bg-slate-950">
        <MapContainer
          center={[
            (layer.bounds_wgs84[1] + layer.bounds_wgs84[3]) / 2,
            (layer.bounds_wgs84[0] + layer.bounds_wgs84[2]) / 2,
          ]}
          zoom={13}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitRasterBounds boundsWgs84={layer.bounds_wgs84} />

          <RasterOverlay
            layer={layer}
            opacity={opacity}
            visible={visible}
          />
        </MapContainer>

        {legendEntries.length > 0 && (
          <div className="absolute bottom-3 right-3 z-[500] max-h-44 max-w-xs overflow-auto rounded-xl border border-slate-700/80 bg-slate-950/90 p-3 shadow-xl backdrop-blur">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Legend
            </p>
            <div className="mt-2 space-y-1.5">
              {legendEntries.map(([label, value]) => {
                const valStr = formatLegendValue(value)
                if (valStr === null) return null
                return (
                  <div
                    key={label}
                    className="flex items-center justify-between gap-3 text-xs"
                  >
                    <span className="text-slate-400">{label}</span>
                    <span className="font-medium text-slate-200">{valStr}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80 bg-slate-900/40 px-5 py-3 text-xs">
        <div className="flex items-center gap-4 text-slate-400">
          <span>
            CRS:{' '}
            <strong className="font-mono text-slate-300">
              {layer.preview_crs || 'EPSG:4326'}
            </strong>
          </span>
          <span>
            Kind:{' '}
            <strong className="font-mono text-slate-300">
              {layer.kind}
            </strong>
          </span>
        </div>

        {layer.download_url ? (
          <a
            href={layer.download_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 font-semibold text-emerald-400 transition hover:text-emerald-300"
          >
            <span>Download GeoTIFF</span>
            <svg
              className="h-3.5 w-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
          </a>
        ) : (
          <span className="text-slate-500">GeoTIFF Unavailable</span>
        )}
      </div>
    </div>
  )
}

function RasterResultMap({
  layers,
  datasetResults = [],
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

  const hasNdvi = useMemo(
    () => displayableLayers.some((l) => l.kind.toLowerCase().includes('ndvi')),
    [displayableLayers],
  )
  const hasWater = useMemo(
    () =>
      displayableLayers.some(
        (l) =>
          l.kind.toLowerCase().includes('water') ||
          l.kind.toLowerCase().includes('mndwi'),
      ),
    [displayableLayers],
  )

  const [activeIndicator, setActiveIndicator] = useState<'ndvi' | 'water'>(
    hasNdvi ? 'ndvi' : 'water',
  )

  useEffect(() => {
    if (!hasNdvi && hasWater) {
      setActiveIndicator('water')
    } else if (hasNdvi && !hasWater) {
      setActiveIndicator('ndvi')
    }
  }, [hasNdvi, hasWater])

  const [visible, setVisible] = useState(true)
  const [opacity, setOpacity] = useState(0.7)

  // Sort dataset results chronologically
  const sortedDatasets = useMemo(
    () =>
      datasetResults.slice().sort((a, b) => {
        const timeA = a.acquisitionDate
          ? new Date(a.acquisitionDate).getTime()
          : (a.year ? new Date(`${a.year}-01-01`).getTime() : 0)
        const timeB = b.acquisitionDate
          ? new Date(b.acquisitionDate).getTime()
          : (b.year ? new Date(`${b.year}-01-01`).getTime() : 0)
        return timeA - timeB
      }),
    [datasetResults],
  )

  // Filter layers for the active indicator
  const indicatorLayers = useMemo(
    () =>
      displayableLayers.filter((l) =>
        activeIndicator === 'ndvi'
          ? l.kind.toLowerCase().includes('ndvi')
          : l.kind.toLowerCase().includes('water') ||
            l.kind.toLowerCase().includes('mndwi'),
      ),
    [displayableLayers, activeIndicator],
  )

  // Dynamically build map panels for all distinct observations
  type MapPanelItem = {
    id: string
    title: string
    subtitle: string
    tag: string
    tagColor: 'blue' | 'emerald' | 'amber'
    layer: RasterResultLayer | null
    metricInfo: string | null
  }

  const panels: MapPanelItem[] = useMemo(() => {
    if (sortedDatasets.length > 0) {
      const total = sortedDatasets.length
      return sortedDatasets.map((dataset, idx) => {
        const matchedLayer =
          indicatorLayers.find((l) => l.dataset_id === dataset.datasetId) ||
          (total === 1 && indicatorLayers.length === 1 ? indicatorLayers[0] : null)

        let tag = 'Observation'
        let tagColor: 'blue' | 'emerald' | 'amber' = 'emerald'

        if (total === 2) {
          tag = idx === 0 ? 'Earlier / Baseline' : 'Later / Latest'
          tagColor = idx === 0 ? 'blue' : 'emerald'
        } else if (total >= 3) {
          if (idx === 0) {
            tag = dataset.year ? `Baseline (${dataset.year})` : 'Baseline'
            tagColor = 'blue'
          } else if (idx === total - 1) {
            tag = dataset.year ? `Latest (${dataset.year})` : 'Latest'
            tagColor = 'emerald'
          } else {
            tag = dataset.year ? `Observation (${dataset.year})` : `Observation ${idx + 1}`
            tagColor = 'amber'
          }
        }

        const title =
          dataset.datasetName ||
          (dataset.year ? `Sentinel-2 Tile (${dataset.year})` : `Observation ${idx + 1}`)

        const subtitle = dataset.acquisitionDate
          ? `Acquisition Date: ${dataset.acquisitionDate}`
          : dataset.year
            ? `Year: ${dataset.year}`
            : 'Observation'

        const metricInfo =
          activeIndicator === 'ndvi'
            ? dataset.ndvi != null
              ? `Mean NDVI: ${dataset.ndvi}`
              : null
            : dataset.waterArea != null
              ? `Water Area: ${dataset.waterArea} ha`
              : null

        return {
          id: dataset.datasetId || `obs-${idx}`,
          title,
          subtitle,
          tag,
          tagColor,
          layer: matchedLayer,
          metricInfo,
        }
      })
    }

    // Fallback if no datasetResults were provided but indicatorLayers exist
    const total = indicatorLayers.length
    return indicatorLayers.map((layer, idx) => {
      let tag = 'Observation'
      let tagColor: 'blue' | 'emerald' | 'amber' = 'emerald'

      if (total === 2) {
        tag = idx === 0 ? 'Earlier / Baseline' : 'Later / Latest'
        tagColor = idx === 0 ? 'blue' : 'emerald'
      } else if (total >= 3) {
        if (idx === 0) {
          tag = 'Baseline'
          tagColor = 'blue'
        } else if (idx === total - 1) {
          tag = 'Latest'
          tagColor = 'emerald'
        } else {
          tag = `Observation ${idx + 1}`
          tagColor = 'amber'
        }
      }

      return {
        id: layer.layer_id || `layer-${idx}`,
        title: layer.kind.toUpperCase(),
        subtitle: layer.dataset_id ? `Dataset ID: ${layer.dataset_id}` : 'Raster Layer',
        tag,
        tagColor,
        layer,
        metricInfo: null,
      }
    })
  }, [sortedDatasets, indicatorLayers, activeIndicator])

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
          No raster result layers are available for this analysis yet. The
          frontend will display backend generated map layers here when they are
          returned.
        </p>
      </section>
    )
  }

  if (displayableLayers.length === 0) {
    return (
      <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-300">
          Raster Result Layers
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          No Displayable Preview
        </h2>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
          Raster layer metadata was returned, but no layer currently has a
          supported WGS84 preview, valid geographic bounds, and a preview URL
          that can be safely placed on this Leaflet map.
        </p>
      </section>
    )
  }

  const panelCount = panels.length

  const badgeText =
    panelCount <= 1
      ? 'Single Observation Map'
      : panelCount === 2
        ? 'Side-by-Side Comparison'
        : `Multi-Date Series (${panelCount} Observations)`

  const descriptionText =
    panelCount <= 1
      ? 'Geospatial preview displaying georeferenced analytical raster layers. Use the indicator buttons and opacity control to inspect ground conditions against base imagery.'
      : panelCount === 2
        ? 'Synchronized side-by-side geospatial preview displaying georeferenced analytical raster layers. Use the indicator buttons and opacity control to inspect ground changes against base imagery.'
        : `Synchronized multi-date geospatial preview displaying ${panelCount} chronologically ordered observations. Inspect raster progression across intermediate and baseline dates.`

  const gridClass =
    panelCount <= 1
      ? 'grid grid-cols-1 max-w-4xl mx-auto gap-6'
      : panelCount === 2
        ? 'grid grid-cols-1 gap-6 lg:grid-cols-2'
        : panelCount === 3
          ? 'grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3'
          : 'grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4'

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 p-6">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex items-center gap-2.5">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
                Spatial Visualizations
              </p>
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                {badgeText}
              </span>
            </div>

            <h2 className="mt-1.5 text-xl font-semibold text-white">
              Year-wise Satellite Impact Comparison
            </h2>

            <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-400">
              {descriptionText}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Indicator switcher */}
            {(hasNdvi || hasWater) && (
              <div className="flex rounded-xl border border-slate-700 bg-slate-950 p-1">
                {hasNdvi && (
                  <button
                    type="button"
                    onClick={() => setActiveIndicator('ndvi')}
                    className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                      activeIndicator === 'ndvi'
                        ? 'bg-emerald-500 text-slate-950 shadow'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Vegetation (NDVI)
                  </button>
                )}
                {hasWater && (
                  <button
                    type="button"
                    onClick={() => setActiveIndicator('water')}
                    className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                      activeIndicator === 'water'
                        ? 'bg-emerald-500 text-slate-950 shadow'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Surface Water (MNDWI)
                  </button>
                )}
              </div>
            )}

            {/* Visibility Toggle */}
            <label className="flex min-h-10 cursor-pointer items-center rounded-xl border border-slate-700 bg-slate-950 px-3.5">
              <input
                type="checkbox"
                checked={visible}
                onChange={(event) => setVisible(event.target.checked)}
                className="h-4 w-4 accent-emerald-500"
              />
              <span className="ml-2 text-xs font-medium text-slate-300">
                Show Layer
              </span>
            </label>

            {/* Opacity Slider */}
            <div className="flex min-h-10 items-center gap-2.5 rounded-xl border border-slate-700 bg-slate-950 px-3.5">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Opacity
              </span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={opacity}
                onChange={(event) => setOpacity(Number(event.target.value))}
                className="w-24 accent-emerald-500"
              />
              <span className="min-w-[36px] font-mono text-xs text-slate-300">
                {Math.round(opacity * 100)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className={gridClass}>
          {panels.map((panel) => (
            <SingleMapPanel
              key={panel.id}
              title={panel.title}
              subtitle={panel.subtitle}
              tag={panel.tag}
              tagColor={panel.tagColor}
              layer={panel.layer}
              opacity={opacity}
              visible={visible}
              metricInfo={panel.metricInfo}
            />
          ))}
        </div>
      </div>

      <div className="border-t border-slate-800 bg-slate-950/30 px-6 py-4">
        <p className="text-xs leading-5 text-slate-500">
          Georeferenced raster overlays are projected in WGS84 (EPSG:4326) and
          aligned across dates to provide honest scientific visual comparison.
          Click "Download GeoTIFF" to obtain the full 32-bit floating point raster
          for external GIS analysis in QGIS or ArcGIS.
        </p>
      </div>
    </section>
  )
}

export default RasterResultMap

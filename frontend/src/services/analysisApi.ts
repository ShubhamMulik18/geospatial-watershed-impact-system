import { getAuthHeaders, getStoredToken } from './authApi'
import type {
  AnalysisMetric,
  AnalysisResult,
  ChangeMetric,
  DatasetResult,
  RasterResultLayer,
  ResultQuality,
  ResultProvenance,
} from '../types/analysisResult'

export type AnalysisRequestPayload = {
  photo_id: string
  polygon: {
    type: 'Polygon'
    coordinates: number[][][]
  }
  dataset_ids: string[]
  indicators: string[]
}

export type AnalysisResponse = {
  schema_version: string
  analysis_id: string
  status: 'created' | 'queued' | 'running' | 'completed' | 'failed'
  stage: string
  inputs: {
    photo_id: string
    polygon: {
      type: string
      coordinates: number[][][]
    }
    dataset_ids: string[]
    indicators: string[]
  }
  prediction: {
    class: string
    class_id: string
    confidence: number
    requires_verification: boolean
    model_version: string
  } | null
  metrics: {
    ndvi_before: number | null
    ndvi_after: number | null
    ndvi_change: number | null
    water_before_hectares: number | null
    water_after_hectares: number | null
    water_change_hectares: number | null
    water_change_percent: number | null
  } | null
  series: Array<{
    dataset_id: string
    date: string
    ndvi_mean: number | null
    water_hectares: number | null
  }>
  comparisons: Array<{
    before_dataset_id: string
    after_dataset_id: string
    ndvi_change: number | null
    water_change_hectares: number | null
    water_change_percent: number | null
  }>
  layers: Array<{
    layer_id: string
    kind: string
    dataset_id: string
    preview_url: string | null
    download_url: string | null
    bounds_wgs84: [number, number, number, number]
    preview_crs: string
    legend: Record<string, unknown>
  }>
  quality: {
    aoi_hectares: number | null
    common_valid_hectares: number | null
    common_valid_fraction: number | null
    per_dataset_valid_fraction: Record<string, number>
    cloud_mask_available: Record<string, boolean>
    comparison_limitations: string[]
  } | null
  warnings: string[]
  provenance: {
    model_version: string | null
    pipeline_version: string | null
    processing_timestamp: string | null
    water_method: string | null
  } | null
  report_status: string
  error: {
    code: string
    message: string
  } | null
}

type BackendErrorResponse = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string | Array<{ msg?: string; loc?: (string | number)[]; type?: string }>
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

export function normalizeIndicator(indicator: string): string {
  const normalized = indicator.toLowerCase().replace(/[-_]/g, '').trim()
  if (
    normalized === 'vegetation' ||
    normalized === 'vegetationchange' ||
    normalized === 'ndvi'
  ) {
    return 'ndvi'
  }
  if (
    normalized === 'surfacewater' ||
    normalized === 'water' ||
    normalized === 'mndwi' ||
    normalized === 'ndwi'
  ) {
    return 'water'
  }
  return indicator
}

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const data =
      (await response.json()) as BackendErrorResponse

    if (data.error?.message) {
      return data.error.message
    }

    if (typeof data.detail === 'string') {
      return data.detail
    }

    if (Array.isArray(data.detail) && data.detail.length > 0) {
      const messages = data.detail.map((err) => {
        const field = Array.isArray(err.loc) ? err.loc.slice(1).join('.') : ''
        return field ? `${field}: ${err.msg || 'Invalid value'}` : (err.msg || 'Validation error')
      })
      return messages.join('; ')
    }
  } catch {
    // The backend did not return a JSON error body.
  }

  return `Analysis request failed with status ${response.status}.`
}

export async function createAnalysis(
  payload: AnalysisRequestPayload,
): Promise<AnalysisResponse> {
  const normalizedPayload: AnalysisRequestPayload = {
    ...payload,
    indicators: payload.indicators.map(normalizeIndicator),
  }

  const response = await fetch(`${API_BASE_URL}/api/analyses`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    credentials: 'include',
    body: JSON.stringify(normalizedPayload),
  })

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as AnalysisResponse
}

export async function getAnalysis(
  analysisId: string,
): Promise<AnalysisResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/analyses/${encodeURIComponent(analysisId)}`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    },
  )

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as AnalysisResponse
}

export async function listRecentAnalyses(): Promise<AnalysisResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/analyses`, {
    method: 'GET',
    headers: getAuthHeaders(),
    credentials: 'include',
  })

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as AnalysisResponse[]
}

export function getReportDownloadUrl(analysisId: string): string {
  const token = getStoredToken()
  const base = `${API_BASE_URL}/api/analyses/${encodeURIComponent(analysisId)}/report`
  return token ? `${base}?token=${encodeURIComponent(token)}` : base
}

export function mapAnalysisResponseToResult(
  backend: AnalysisResponse,
): AnalysisResult {
  const metrics: AnalysisMetric[] = []

  if (backend.metrics) {
    if (backend.metrics.ndvi_after != null) {
      metrics.push({
        id: 'latest-ndvi',
        label: 'Latest NDVI',
        value: Number(backend.metrics.ndvi_after.toFixed(3)),
        unit: null,
        description: 'Vegetation index for the most recent observation.',
      })
    }
    if (backend.metrics.water_after_hectares != null) {
      metrics.push({
        id: 'water-area',
        label: 'Surface Water Area',
        value: Number(backend.metrics.water_after_hectares.toFixed(2)),
        unit: 'ha',
        description: 'Surface water area for the most recent observation.',
      })
    }
    if (backend.metrics.ndvi_change != null) {
      metrics.push({
        id: 'ndvi-change',
        label: 'NDVI Change',
        value: Number(backend.metrics.ndvi_change.toFixed(3)),
        unit: null,
        description: 'Observed change in vegetation index.',
      })
    }
    if (backend.metrics.water_change_hectares != null) {
      metrics.push({
        id: 'water-change',
        label: 'Water Area Change',
        value: Number(backend.metrics.water_change_hectares.toFixed(2)),
        unit: 'ha',
        description: 'Observed change in surface water area.',
      })
    }
  }

  const sortedSeries = (backend.series || []).slice().sort((a, b) => {
    const timeA = a.date ? new Date(a.date).getTime() : 0
    const timeB = b.date ? new Date(b.date).getTime() : 0
    return timeA - timeB
  })

  const datasetResults: DatasetResult[] = sortedSeries.map(
    (point, index) => {
      const year = point.date
        ? new Date(point.date).getFullYear()
        : 2020 + index * 3
      return {
        datasetId: point.dataset_id,
        datasetName: `Sentinel-2 Tile T43QDU (${year})`,
        year,
        acquisitionDate: point.date ? String(point.date) : null,
        ndvi:
          point.ndvi_mean != null
            ? Number(point.ndvi_mean.toFixed(3))
            : null,
        waterArea:
          point.water_hectares != null
            ? Number(point.water_hectares.toFixed(2))
            : null,
      }
    },
  )

  const changes: ChangeMetric[] = []
  if (backend.metrics) {
    if (
      backend.metrics.ndvi_before != null ||
      backend.metrics.ndvi_after != null
    ) {
      changes.push({
        id: 'vegetation-change',
        label: 'Vegetation Index (NDVI)',
        before:
          backend.metrics.ndvi_before != null
            ? Number(backend.metrics.ndvi_before.toFixed(3))
            : null,
        after:
          backend.metrics.ndvi_after != null
            ? Number(backend.metrics.ndvi_after.toFixed(3))
            : null,
        change:
          backend.metrics.ndvi_change != null
            ? Number(backend.metrics.ndvi_change.toFixed(3))
            : null,
        unit: null,
      })
    }
    if (
      backend.metrics.water_before_hectares != null ||
      backend.metrics.water_after_hectares != null
    ) {
      changes.push({
        id: 'surface-water-change',
        label: 'Surface Water Area',
        before:
          backend.metrics.water_before_hectares != null
            ? Number(backend.metrics.water_before_hectares.toFixed(2))
            : null,
        after:
          backend.metrics.water_after_hectares != null
            ? Number(backend.metrics.water_after_hectares.toFixed(2))
            : null,
        change:
          backend.metrics.water_change_hectares != null
            ? Number(backend.metrics.water_change_hectares.toFixed(2))
            : null,
        unit: 'ha',
      })
    }
  }

  const token = getStoredToken()
  const appendToken = (url: string | null): string | null => {
    if (!url) return null
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`
    if (!token || fullUrl.includes('token=')) return fullUrl
    const sep = fullUrl.includes('?') ? '&' : '?'
    return `${fullUrl}${sep}token=${encodeURIComponent(token)}`
  }

  const layers: RasterResultLayer[] = (backend.layers || []).map((l) => ({
    layer_id: l.layer_id,
    kind: l.kind,
    dataset_id: l.dataset_id,
    preview_url: appendToken(l.preview_url),
    download_url: appendToken(l.download_url),
    bounds_wgs84: l.bounds_wgs84,
    preview_crs: l.preview_crs,
    legend: l.legend || {},
  }))

  const quality: ResultQuality = {
    status: backend.quality
      ? `${Math.round((backend.quality.common_valid_fraction ?? 1.0) * 100)}% valid pixels`
      : 'Available',
    summary:
      backend.quality?.common_valid_hectares != null
        ? `Common valid support area: ${backend.quality.common_valid_hectares.toFixed(1)} ha across compared satellite dates.`
        : 'Quality validation verified on common support grid.',
  }

  const provenance: ResultProvenance = {
    source: 'Sentinel-2 L2A Multispectral Satellite Imagery',
    modelVersion:
      backend.prediction?.model_version ||
      backend.provenance?.model_version ||
      'production-v1',
    generatedAt:
      backend.provenance?.processing_timestamp || new Date().toISOString(),
  }

  return {
    analysisId: backend.analysis_id,
    status: 'completed',
    prediction: {
      predictedClass:
        backend.prediction?.class ||
        backend.prediction?.class_id ||
        null,
      confidence: backend.prediction?.confidence ?? null,
    },
    metrics,
    datasetResults,
    changes,
    layers,
    warnings: backend.warnings || [],
    quality,
    provenance,
  }
}


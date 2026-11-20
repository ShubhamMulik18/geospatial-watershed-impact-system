export type ResultValue = number | null

export type AnalysisMetric = {
  id: string
  label: string
  value: ResultValue
  unit: string | null
  description: string | null
}

export type DatasetResult = {
  datasetId: string
  datasetName: string
  year: number | null
  acquisitionDate: string | null

  ndvi: ResultValue
  waterArea: ResultValue
}

export type ChangeMetric = {
  id: string
  label: string
  before: ResultValue
  after: ResultValue
  change: ResultValue
  unit: string | null
}

export type ResultQuality = {
  status: string | null
  summary: string | null
}

export type ResultProvenance = {
  source: string | null
  modelVersion: string | null
  generatedAt: string | null
}

/*
 * Backend LayerDescriptor currently defines legend as:
 *
 * dict[str, object]
 *
 * We intentionally do not invent a more specific legend structure
 * until the backend guarantees one.
 */
export type RasterLegend = Record<string, unknown>

/*
 * Frontend representation of the backend LayerDescriptor.
 *
 * bounds_wgs84 order:
 * [left, bottom, right, top]
 *
 * The frontend must use these backend-provided bounds.
 * It must never infer geographic bounds from preview image pixels.
 */
export type RasterResultLayer = {
  layer_id: string
  kind: string
  dataset_id: string

  preview_url: string | null
  download_url: string | null

  bounds_wgs84: [number, number, number, number]

  preview_crs: string

  legend: RasterLegend
}

export type AnalysisResult = {
  analysisId: string
  status: 'completed'

  prediction: {
    predictedClass: string | null
    confidence: ResultValue
  }

  metrics: AnalysisMetric[]
  datasetResults: DatasetResult[]
  changes: ChangeMetric[]

  layers: RasterResultLayer[]

  warnings: string[]

  quality: ResultQuality
  provenance: ResultProvenance
}
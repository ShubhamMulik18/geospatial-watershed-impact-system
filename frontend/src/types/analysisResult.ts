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

  warnings: string[]

  quality: ResultQuality
  provenance: ResultProvenance
}
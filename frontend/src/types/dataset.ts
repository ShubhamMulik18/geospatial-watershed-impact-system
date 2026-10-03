export type DatasetQuality = {
  status: 'available' | 'unavailable'
  summary: string | null
}

export type DatasetMetadata = {
  id: string
  displayName: string
  year: number | null
  acquisitionDate: string | null
  coverage: string | null
  resolution: string | null
  supportedIndicators: string[]
  waterMethods: string[]
  warnings: string[]
  quality: DatasetQuality
  isCompatible: boolean
  incompatibilityReason: string | null
}
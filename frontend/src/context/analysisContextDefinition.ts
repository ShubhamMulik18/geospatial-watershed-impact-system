import { createContext } from 'react'

import type { StudyAreaPolygon } from '../components/map/PolygonEditor'
import type { PhotoMetadataData } from '../components/photo/PhotoMetadata'
import type { PredictionData } from '../components/photo/PredictionCard'
import type { DatasetMetadata } from '../types/dataset'

export type AnalysisContextValue = {
  photoId: string | null
  photoMetadata: PhotoMetadataData | null

  predictionId: string | null
  prediction: PredictionData | null

  draftPolygon: StudyAreaPolygon | null
  confirmedPolygon: StudyAreaPolygon | null

  datasetIds: string[]
  selectedDatasets: DatasetMetadata[]
  indicators: string[]

  analysisId: string | null

  validationIsStale: boolean
  resultsAreStale: boolean
  isSubmitting: boolean

  setPhoto: (
    photoId: string | null,
    metadata: PhotoMetadataData | null,
  ) => void

  setPrediction: (
    predictionId: string | null,
    prediction: PredictionData | null,
  ) => void

  setDraftPolygon: (
    polygon: StudyAreaPolygon | null,
  ) => void

  confirmPolygon: (
    polygon: StudyAreaPolygon,
  ) => void

  setDatasetIds: (
    datasetIds: string[],
  ) => void

  setSelectedDatasets: (
    datasets: DatasetMetadata[],
  ) => void

  setIndicators: (
    indicators: string[],
  ) => void

  setAnalysisId: (
    analysisId: string | null,
  ) => void

  markValidationFresh: () => void
  markResultsFresh: () => void

  beginPhotoRequest: () => number
  isCurrentPhotoRequest: (requestId: number) => boolean

  beginSubmission: () => number | null
  finishSubmission: (requestId: number) => boolean

  resetAnalysis: () => void
}

export const AnalysisContext = createContext<
  AnalysisContextValue | undefined
>(undefined)
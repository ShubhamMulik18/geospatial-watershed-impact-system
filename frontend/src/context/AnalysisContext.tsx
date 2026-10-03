import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

import type { StudyAreaPolygon } from '../components/map/PolygonEditor'
import type { PhotoMetadataData } from '../components/photo/PhotoMetadata'
import type { PredictionData } from '../components/photo/PredictionCard'
import {
  AnalysisContext,
  type AnalysisContextValue,
} from './analysisContextDefinition'

type AnalysisProviderProps = {
  children: ReactNode
}

export function AnalysisProvider({
  children,
}: AnalysisProviderProps) {
  const [photoId, setPhotoId] = useState<string | null>(null)

  const [photoMetadata, setPhotoMetadata] =
    useState<PhotoMetadataData | null>(null)

  const [predictionId, setPredictionId] =
    useState<string | null>(null)

  const [prediction, setPredictionState] =
    useState<PredictionData | null>(null)

  const [draftPolygon, setDraftPolygonState] =
    useState<StudyAreaPolygon | null>(null)

  const [confirmedPolygon, setConfirmedPolygon] =
    useState<StudyAreaPolygon | null>(null)

  const [datasetIds, setDatasetIdsState] =
    useState<string[]>([])

  const [indicators, setIndicatorsState] =
    useState<string[]>([])

  const [analysisId, setAnalysisIdState] =
    useState<string | null>(null)

  const [validationIsStale, setValidationIsStale] =
    useState(false)

  const [resultsAreStale, setResultsAreStale] =
    useState(false)

  const [isSubmitting, setIsSubmitting] =
    useState(false)

  const photoRequestCounterRef = useRef(0)
  const currentPhotoRequestRef = useRef(0)

  const analysisRequestCounterRef = useRef(0)
  const activeAnalysisRequestRef =
    useRef<number | null>(null)

  const confirmedPolygonRef =
    useRef<StudyAreaPolygon | null>(null)

  const invalidateAnalysis = useCallback(() => {
    setValidationIsStale(true)
    setResultsAreStale(true)
    setAnalysisIdState(null)
  }, [])

  const handleSetPhoto = useCallback(
    (
      nextPhotoId: string | null,
      metadata: PhotoMetadataData | null,
    ) => {
      setPhotoId(nextPhotoId)
      setPhotoMetadata(metadata)

      setPredictionId(null)
      setPredictionState(null)

      setDraftPolygonState(null)

      confirmedPolygonRef.current = null
      setConfirmedPolygon(null)

      setDatasetIdsState([])
      setIndicatorsState([])

      setAnalysisIdState(null)

      setValidationIsStale(false)
      setResultsAreStale(false)

      activeAnalysisRequestRef.current = null
      setIsSubmitting(false)
    },
    [],
  )

  const handleSetPrediction = useCallback(
    (
      nextPredictionId: string | null,
      nextPrediction: PredictionData | null,
    ) => {
      setPredictionId(nextPredictionId)
      setPredictionState(nextPrediction)
    },
    [],
  )

  const handleSetDraftPolygon = useCallback(
    (polygon: StudyAreaPolygon | null) => {
      setDraftPolygonState(polygon)

      if (confirmedPolygonRef.current !== null) {
        confirmedPolygonRef.current = null
        setConfirmedPolygon(null)

        invalidateAnalysis()
      }
    },
    [invalidateAnalysis],
  )

  const handleConfirmPolygon = useCallback(
    (polygon: StudyAreaPolygon) => {
      setDraftPolygonState(polygon)

      confirmedPolygonRef.current = polygon
      setConfirmedPolygon(polygon)
    },
    [],
  )

  const handleSetDatasetIds = useCallback(
    (nextDatasetIds: string[]) => {
      setDatasetIdsState(nextDatasetIds)
      invalidateAnalysis()
    },
    [invalidateAnalysis],
  )

  const handleSetIndicators = useCallback(
    (nextIndicators: string[]) => {
      setIndicatorsState(nextIndicators)
      invalidateAnalysis()
    },
    [invalidateAnalysis],
  )

  const handleSetAnalysisId = useCallback(
    (nextAnalysisId: string | null) => {
      setAnalysisIdState(nextAnalysisId)
    },
    [],
  )

  const markValidationFresh = useCallback(() => {
    setValidationIsStale(false)
  }, [])

  const markResultsFresh = useCallback(() => {
    setResultsAreStale(false)
  }, [])

  const beginPhotoRequest = useCallback(() => {
    photoRequestCounterRef.current += 1

    const requestId = photoRequestCounterRef.current

    currentPhotoRequestRef.current = requestId

    return requestId
  }, [])

  const isCurrentPhotoRequest = useCallback(
    (requestId: number) => {
      return currentPhotoRequestRef.current === requestId
    },
    [],
  )

  const beginSubmission = useCallback(() => {
    if (activeAnalysisRequestRef.current !== null) {
      return null
    }

    analysisRequestCounterRef.current += 1

    const requestId =
      analysisRequestCounterRef.current

    activeAnalysisRequestRef.current = requestId
    setIsSubmitting(true)

    return requestId
  }, [])

  const finishSubmission = useCallback(
    (requestId: number) => {
      if (
        activeAnalysisRequestRef.current !== requestId
      ) {
        return false
      }

      activeAnalysisRequestRef.current = null
      setIsSubmitting(false)

      return true
    },
    [],
  )

  const resetAnalysis = useCallback(() => {
    photoRequestCounterRef.current += 1
    currentPhotoRequestRef.current =
      photoRequestCounterRef.current

    analysisRequestCounterRef.current += 1
    activeAnalysisRequestRef.current = null

    setPhotoId(null)
    setPhotoMetadata(null)

    setPredictionId(null)
    setPredictionState(null)

    setDraftPolygonState(null)

    confirmedPolygonRef.current = null
    setConfirmedPolygon(null)

    setDatasetIdsState([])
    setIndicatorsState([])

    setAnalysisIdState(null)

    setValidationIsStale(false)
    setResultsAreStale(false)

    setIsSubmitting(false)
  }, [])

  const value = useMemo<AnalysisContextValue>(
    () => ({
      photoId,
      photoMetadata,

      predictionId,
      prediction,

      draftPolygon,
      confirmedPolygon,

      datasetIds,
      indicators,

      analysisId,

      validationIsStale,
      resultsAreStale,
      isSubmitting,

      setPhoto: handleSetPhoto,
      setPrediction: handleSetPrediction,

      setDraftPolygon: handleSetDraftPolygon,
      confirmPolygon: handleConfirmPolygon,

      setDatasetIds: handleSetDatasetIds,
      setIndicators: handleSetIndicators,

      setAnalysisId: handleSetAnalysisId,

      markValidationFresh,
      markResultsFresh,

      beginPhotoRequest,
      isCurrentPhotoRequest,

      beginSubmission,
      finishSubmission,

      resetAnalysis,
    }),
    [
      photoId,
      photoMetadata,
      predictionId,
      prediction,
      draftPolygon,
      confirmedPolygon,
      datasetIds,
      indicators,
      analysisId,
      validationIsStale,
      resultsAreStale,
      isSubmitting,
      handleSetPhoto,
      handleSetPrediction,
      handleSetDraftPolygon,
      handleConfirmPolygon,
      handleSetDatasetIds,
      handleSetIndicators,
      handleSetAnalysisId,
      markValidationFresh,
      markResultsFresh,
      beginPhotoRequest,
      isCurrentPhotoRequest,
      beginSubmission,
      finishSubmission,
      resetAnalysis,
    ],
  )

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  )
}
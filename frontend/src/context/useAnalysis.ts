import { useContext } from 'react'

import { AnalysisContext } from './analysisContextDefinition'

export function useAnalysis() {
  const context = useContext(AnalysisContext)

  if (!context) {
    throw new Error(
      'useAnalysis must be used inside an AnalysisProvider.',
    )
  }

  return context
}
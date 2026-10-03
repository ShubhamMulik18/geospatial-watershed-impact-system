import type { AnalysisResult } from '../types/analysisResult'

export const mockAnalysisResult: AnalysisResult = {
  analysisId: 'mock-analysis',

  status: 'completed',

  prediction: {
    predictedClass: 'Check Dam',
    confidence: 0.91,
  },

  metrics: [
    {
      id: 'latest-ndvi',
      label: 'Latest NDVI',
      value: 0.58,
      unit: null,
      description: 'Demo NDVI value for the latest mock dataset.',
    },
    {
      id: 'water-area',
      label: 'Surface Water Area',
      value: 14.7,
      unit: 'ha',
      description: 'Demo surface-water area for the mock analysis.',
    },
    {
      id: 'ndvi-change',
      label: 'NDVI Change',
      value: 0.12,
      unit: null,
      description: 'Demo before-and-after vegetation change.',
    },
    {
      id: 'water-change',
      label: 'Water Area Change',
      value: 2.3,
      unit: 'ha',
      description: 'Demo before-and-after surface-water change.',
    },
  ],

  datasetResults: [
    {
      datasetId: 'mock-dataset-2022',
      datasetName: 'Demo Watershed Dataset — 2022',
      year: 2022,
      acquisitionDate: '2022-11-15',
      ndvi: 0.46,
      waterArea: 12.4,
    },
    {
      datasetId: 'mock-dataset-2024',
      datasetName: 'Demo Watershed Dataset — 2024',
      year: 2024,
      acquisitionDate: '2024-11-18',
      ndvi: 0.53,
      waterArea: 13.8,
    },
    {
      datasetId: 'mock-dataset-2025',
      datasetName: 'Demo Watershed Dataset — 2025',
      year: 2025,
      acquisitionDate: '2025-11-20',
      ndvi: 0.58,
      waterArea: 14.7,
    },
  ],

  changes: [
    {
      id: 'vegetation-change',
      label: 'Vegetation Index',
      before: 0.46,
      after: 0.58,
      change: 0.12,
      unit: null,
    },
    {
      id: 'surface-water-change',
      label: 'Surface Water Area',
      before: 12.4,
      after: 14.7,
      change: 2.3,
      unit: 'ha',
    },
  ],

  warnings: [
    'Mock result only — no satellite processing or backend watershed analysis was performed.',
    'Values shown on this page are demonstration data and must not be used for scientific interpretation.',
  ],

  quality: {
    status: 'Demo only',
    summary:
      'Quality information is simulated for the frontend mock workflow and does not represent validated analysis quality.',
  },

  provenance: {
    source: 'Frontend mock workflow',
    modelVersion: 'mock-demo-model',
    generatedAt: null,
  },
}
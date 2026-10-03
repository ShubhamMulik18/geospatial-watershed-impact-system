import type {
  AnalysisModeOption,
} from '../components/analysis/AnalysisControls'
import type {
  IndicatorOption,
} from '../components/analysis/IndicatorSelector'
import type {
  PredictionData,
} from '../components/photo/PredictionCard'
import type {
  DatasetMetadata,
} from '../types/dataset'

export const mockDatasets: DatasetMetadata[] = [
  {
    id: 'mock-dataset-2022',
    displayName: 'Demo Watershed Dataset — 2022',
    year: 2022,
    acquisitionDate: '2022-11-15',
    coverage: 'Demo study-area coverage',
    resolution: '10 m',
    supportedIndicators: [
      'vegetation',
      'surface-water',
    ],
    waterMethods: [
      'Demo water-index method',
    ],
    warnings: [
      'Mock dataset for frontend demonstration only.',
    ],
    quality: {
      status: 'available',
      summary:
        'Mock quality information for frontend testing.',
    },
    isCompatible: true,
    incompatibilityReason: null,
  },

  {
    id: 'mock-dataset-2024',
    displayName: 'Demo Watershed Dataset — 2024',
    year: 2024,
    acquisitionDate: '2024-11-18',
    coverage: 'Demo study-area coverage',
    resolution: '10 m',
    supportedIndicators: [
      'vegetation',
      'surface-water',
    ],
    waterMethods: [
      'Demo water-index method',
    ],
    warnings: [
      'Mock dataset for frontend demonstration only.',
    ],
    quality: {
      status: 'available',
      summary:
        'Mock quality information for frontend testing.',
    },
    isCompatible: true,
    incompatibilityReason: null,
  },

  {
    id: 'mock-dataset-2025',
    displayName: 'Demo Watershed Dataset — 2025',
    year: 2025,
    acquisitionDate: '2025-11-20',
    coverage: 'Demo study-area coverage',
    resolution: '10 m',
    supportedIndicators: [
      'vegetation',
      'surface-water',
    ],
    waterMethods: [
      'Demo water-index method',
    ],
    warnings: [
      'Mock dataset for frontend demonstration only.',
    ],
    quality: {
      status: 'available',
      summary:
        'Mock quality information for frontend testing.',
    },
    isCompatible: true,
    incompatibilityReason: null,
  },
]

export const mockIndicators: IndicatorOption[] = [
  {
    id: 'vegetation',
    displayName: 'Vegetation Change',
    description:
      'Mock indicator for demonstrating vegetation-change selection.',
    isSupported: true,
    unsupportedReason: null,
  },

  {
    id: 'surface-water',
    displayName: 'Surface Water Change',
    description:
      'Mock indicator for demonstrating surface-water change selection.',
    isSupported: true,
    unsupportedReason: null,
  },
]

export const mockAnalysisModes: AnalysisModeOption[] = [
  {
    id: 'before-after',
    displayName: 'Before / After',
    description:
      'Compare two selected mock dataset dates.',
    isAvailable: true,
    unavailableReason: null,
  },

  {
    id: 'multi-date',
    displayName: 'Multi-date Series',
    description:
      'Compare change across multiple selected mock dataset dates.',
    isAvailable: true,
    unavailableReason: null,
  },
]

export const mockPrediction: PredictionData = {
  predictedClass: 'Check Dam',
  confidence: 0.91,
  verificationRequired: true,
  modelVersion: 'mock-demo-model',
  warnings: [
    'Mock AI prediction for frontend demonstration only.',
  ],
}
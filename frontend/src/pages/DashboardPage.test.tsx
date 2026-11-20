import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import DashboardPage from './DashboardPage'
import * as analysisApi from '../services/analysisApi'
import * as datasetApi from '../services/datasetApi'

const mockAnalysisResponses: analysisApi.AnalysisResponse[] = [
  {
    schema_version: '1.0',
    analysis_id: 'analysis-123',
    status: 'completed',
    stage: 'completed',
    inputs: {
      photo_id: 'photo-1',
      polygon: { type: 'Polygon', coordinates: [] },
      dataset_ids: ['ds-1', 'ds-2', 'ds-3'],
      indicators: ['ndvi', 'water'],
    },
    prediction: {
      class: 'Check Dam',
      class_id: 'check_dam',
      confidence: 0.88,
      requires_verification: false,
      model_version: 'v1',
    },
    metrics: null,
    series: [],
    comparisons: [],
    layers: [],
    quality: null,
    warnings: [],
    provenance: null,
    report_status: 'not_requested',
    error: null,
  },
  {
    schema_version: '1.0',
    analysis_id: 'analysis-456',
    status: 'running',
    stage: 'processing',
    inputs: {
      photo_id: 'photo-2',
      polygon: { type: 'Polygon', coordinates: [] },
      dataset_ids: ['ds-1', 'ds-2'],
      indicators: ['ndvi'],
    },
    prediction: {
      class: 'Contour Trench',
      class_id: 'contour_trench',
      confidence: 0.75,
      requires_verification: false,
      model_version: 'v1',
    },
    metrics: null,
    series: [],
    comparisons: [],
    layers: [],
    quality: null,
    warnings: [],
    provenance: null,
    report_status: 'not_requested',
    error: null,
  },
]

const mockDatasets = [
  {
    id: 'ds-1',
    displayName: 'Sentinel-2 2026',
    year: 2026,
    acquisitionDate: '2026-09-15',
    coverage: 'Coverage available',
    resolution: '10 m',
    supportedIndicators: ['ndvi', 'water'],
    waterMethods: ['ndwi', 'mndwi'],
    warnings: [],
    quality: { status: 'available' as const, summary: null },
    isCompatible: true,
    incompatibilityReason: null,
  },
  {
    id: 'ds-2',
    displayName: 'Sentinel-2 2025',
    year: 2025,
    acquisitionDate: '2025-09-15',
    coverage: 'Coverage available',
    resolution: '10 m',
    supportedIndicators: ['ndvi', 'water'],
    waterMethods: ['ndwi', 'mndwi'],
    warnings: [],
    quality: { status: 'available' as const, summary: null },
    isCompatible: true,
    incompatibilityReason: null,
  },
]

describe('DashboardPage Initial Startup Data Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(analysisApi, 'listRecentAnalyses').mockResolvedValue(
      mockAnalysisResponses,
    )
    vi.spyOn(datasetApi, 'getDatasets').mockResolvedValue(mockDatasets)
  })

  it('renders real persisted analysis data and statistics on successful fetch', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    )

    // Check header
    expect(
      screen.getByRole('heading', { name: /watershed dashboard/i }),
    ).toBeInTheDocument()

    // Wait for analyses to load and render table
    await waitFor(() => {
      expect(screen.getByText('Check Dam')).toBeInTheDocument()
      expect(screen.getByText('Contour Trench')).toBeInTheDocument()
    })

    // Check stats are computed correctly
    expect(screen.getAllByText('2').length).toBeGreaterThanOrEqual(1) // Total Analyses / Datasets
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1) // Completed / Processing Analyses
  })

  it('displays empty state banner when no analyses have been submitted', async () => {
    vi.spyOn(analysisApi, 'listRecentAnalyses').mockResolvedValue([])

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(
        screen.getByText(/no analyses recorded yet/i),
      ).toBeInTheDocument()
    })
  })

  it('displays warning banner when analysis fetch fails', async () => {
    vi.spyOn(analysisApi, 'listRecentAnalyses').mockRejectedValue(
      new Error('Failed to fetch analyses'),
    )

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(
        screen.getByText(/failed to load recent analyses/i),
      ).toBeInTheDocument()
    })
  })

  it('displays warning banner when dataset catalogue fetch fails', async () => {
    vi.spyOn(datasetApi, 'getDatasets').mockRejectedValue(
      new Error('Failed to fetch datasets'),
    )

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(
        screen.getByText(/failed to load dataset catalogue/i),
      ).toBeInTheDocument()
    })
  })
})

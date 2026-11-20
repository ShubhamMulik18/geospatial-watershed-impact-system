import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createAnalysis,
  getAnalysis,
  listRecentAnalyses,
  getReportDownloadUrl,
  mapAnalysisResponseToResult,
} from './analysisApi'
import type { AnalysisResponse } from './analysisApi'

function createMockAnalysisResponse(overrides: Partial<AnalysisResponse> = {}): AnalysisResponse {
  return {
    schema_version: '1.0',
    analysis_id: 'ana-test-1',
    status: 'created',
    stage: 'queued',
    inputs: {
      photo_id: 'photo-1',
      polygon: {
        type: 'Polygon',
        coordinates: [[[74.2, 16.6], [74.3, 16.6], [74.3, 16.7], [74.2, 16.7], [74.2, 16.6]]],
      },
      dataset_ids: ['ds-1', 'ds-2'],
      indicators: ['ndvi', 'mndwi'],
    },
    prediction: null,
    metrics: null,
    series: [],
    comparisons: [],
    layers: [],
    quality: null,
    warnings: [],
    provenance: null,
    report_status: 'pending',
    error: null,
    ...overrides,
  }
}

describe('analysisApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('createAnalysis posts data and returns analysis response', async () => {
    const mockResponse = createMockAnalysisResponse({ status: 'queued' })

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockResponse), {
        status: 202,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const payload = {
      photo_id: 'photo-1',
      polygon: {
        type: 'Polygon' as const,
        coordinates: [[[74.2, 16.6], [74.3, 16.6], [74.3, 16.7], [74.2, 16.7], [74.2, 16.6]]],
      },
      dataset_ids: ['ds-1', 'ds-2'],
      indicators: ['ndvi', 'mndwi'],
    }

    const res = await createAnalysis(payload)
    expect(res).toEqual(mockResponse)
  })

  it('getAnalysis retrieves specific analysis by ID', async () => {
    const mockResponse = createMockAnalysisResponse({
      analysis_id: 'ana-123',
      status: 'completed',
      stage: 'completed',
      layers: [
        {
          layer_id: 'layer-ndvi',
          kind: 'ndvi',
          dataset_id: 'ds-2023',
          preview_url: '/api/analyses/ana-123/artifacts/art-1',
          download_url: '/api/analyses/ana-123/artifacts/art-2',
          bounds_wgs84: [74.2, 16.6, 74.3, 16.7],
          preview_crs: 'EPSG:4326',
          legend: {},
        },
      ],
    })

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const res = await getAnalysis('ana-123')
    expect(res.analysis_id).toBe('ana-123')
    expect(res.status).toBe('completed')
    expect(res.layers?.length).toBe(1)
  })

  it('listRecentAnalyses fetches list of analyses', async () => {
    const mockList = [createMockAnalysisResponse({ analysis_id: 'ana-1', status: 'completed' })]

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockList), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const res = await listRecentAnalyses()
    expect(res).toEqual(mockList)
  })

  it('getReportDownloadUrl constructs valid endpoint URL', () => {
    expect(getReportDownloadUrl('ana-999')).toBe(
      'http://localhost:8000/api/analyses/ana-999/report',
    )
  })

  it('mapAnalysisResponseToResult converts backend response to UI model', () => {
    const backendData = createMockAnalysisResponse({
      analysis_id: 'test-run-1',
      status: 'completed',
      stage: 'completed',
      prediction: {
        class: 'Check Dam',
        class_id: 'check_dam',
        confidence: 0.95,
        requires_verification: false,
        model_version: 'mobilenetv2_v1',
      },
      layers: [
        {
          layer_id: 'l1',
          kind: 'ndvi',
          dataset_id: 'ds-2023',
          preview_url: '/api/analyses/test-run-1/artifacts/p1',
          download_url: '/api/analyses/test-run-1/artifacts/r1',
          bounds_wgs84: [74.2, 16.6, 74.3, 16.7],
          preview_crs: 'EPSG:4326',
          legend: {},
        },
      ],
      metrics: {
        ndvi_before: 0.35,
        ndvi_after: 0.45,
        ndvi_change: 0.1,
        water_before_hectares: 10.0,
        water_after_hectares: 12.5,
        water_change_hectares: 2.5,
        water_change_percent: 25.0,
      },
      series: [
        {
          dataset_id: 'ds-2020',
          date: '2020-03-01',
          ndvi_mean: 0.35,
          water_hectares: 10.0,
        },
        {
          dataset_id: 'ds-2023',
          date: '2023-03-01',
          ndvi_mean: 0.45,
          water_hectares: 12.5,
        },
      ],
      quality: {
        aoi_hectares: 150.0,
        common_valid_hectares: 147.0,
        common_valid_fraction: 0.98,
        per_dataset_valid_fraction: { 'ds-2020': 0.99, 'ds-2023': 0.98 },
        cloud_mask_available: { 'ds-2020': true, 'ds-2023': true },
        comparison_limitations: [],
      },
    })

    const mapped = mapAnalysisResponseToResult(backendData)
    expect(mapped.analysisId).toBe('test-run-1')
    expect(mapped.prediction.predictedClass).toBe('Check Dam')
    expect(mapped.prediction.confidence).toBe(0.95)
    expect(mapped.metrics.length).toBeGreaterThanOrEqual(3)
    expect(mapped.datasetResults.length).toBe(2)
    expect(mapped.changes.length).toBe(2)
    expect(mapped.layers.length).toBe(1)
  })
})


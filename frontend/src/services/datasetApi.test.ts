import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { getDatasets } from './datasetApi'

describe('datasetApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('maps backend dataset responses to frontend metadata', async () => {
    const backendResponse = [
      {
        dataset_id: 'dataset-123',
        display_name: 'Watershed 2025',
        year: 2025,
        coverage_available: true,
        acquisition_date: '2025-01-15',
        supported_indicators: ['vegetation_change'],
        water_methods: ['ndwi'],
        bounds_wgs84: [73.5, 16.9, 73.6, 17.0],
        resolution_metres: 10,
        quality_mask_available: true,
        warnings: ['Example warning'],
      },
    ]

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(backendResponse), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }),
    )

    const datasets = await getDatasets()

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/datasets',
    )

    expect(datasets).toHaveLength(1)

    expect(datasets[0]).toEqual({
      id: 'dataset-123',
      displayName: 'Watershed 2025',
      year: 2025,
      acquisitionDate: '2025-01-15',
      coverage: 'Coverage available',
      resolution: '10 m',
      supportedIndicators: ['vegetation_change'],
      waterMethods: ['ndwi'],
      warnings: ['Example warning'],
      quality: {
        status: 'available',
        summary: 'Quality mask available',
      },
      isCompatible: true,
      incompatibilityReason: null,
    })
  })

  it('marks datasets without coverage as incompatible', async () => {
    const backendResponse = [
      {
        dataset_id: 'dataset-456',
        display_name: 'Unavailable Coverage',
        year: 2024,
        coverage_available: false,
        acquisition_date: '2024-01-15',
        supported_indicators: [],
        water_methods: [],
        bounds_wgs84: [73.5, 16.9, 73.6, 17.0],
        resolution_metres: null,
        quality_mask_available: false,
        warnings: [],
      },
    ]

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(backendResponse), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }),
    )

    const datasets = await getDatasets()

    expect(datasets[0].isCompatible).toBe(false)
    expect(datasets[0].coverage).toBe(
      'Coverage unavailable',
    )
    expect(datasets[0].resolution).toBeNull()
    expect(datasets[0].quality.status).toBe(
      'unavailable',
    )
    expect(
      datasets[0].incompatibilityReason,
    ).toBe('Dataset coverage is unavailable.')
  })

  it('uses the backend error message when a request fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'dataset_error',
            message: 'Dataset catalogue unavailable.',
          },
        }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    )

    await expect(getDatasets()).rejects.toThrow(
      'Dataset catalogue unavailable.',
    )
  })
})
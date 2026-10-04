import type { DatasetMetadata } from '../types/dataset'

export type DatasetResponse = {
  dataset_id: string
  display_name: string
  year: number
  coverage_available: boolean
  acquisition_date: string
  supported_indicators: string[]
  water_methods: string[]
  bounds_wgs84: [
    number,
    number,
    number,
    number,
  ]
  resolution_metres: number | null
  quality_mask_available: boolean
  warnings: string[]
}

export type DatasetUploadInput = {
  file: File
  displayName: string
  acquisitionDate: string
  capabilities: string[]
  waterMethods: string[]
}

type BackendErrorResponse = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000'

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const data =
      (await response.json()) as BackendErrorResponse

    if (data.error?.message) {
      return data.error.message
    }

    if (typeof data.detail === 'string') {
      return data.detail
    }
  } catch {
    // Fall back to the HTTP status message below.
  }

  return `Dataset request failed with status ${response.status}.`
}

function mapDatasetResponse(
  dataset: DatasetResponse,
): DatasetMetadata {
  return {
    id: dataset.dataset_id,
    displayName: dataset.display_name,
    year: dataset.year,
    acquisitionDate: dataset.acquisition_date,

    coverage: dataset.coverage_available
      ? 'Coverage available'
      : 'Coverage unavailable',

    resolution:
      dataset.resolution_metres !== null
        ? `${dataset.resolution_metres} m`
        : null,

    supportedIndicators:
      dataset.supported_indicators,

    waterMethods:
      dataset.water_methods,

    warnings: dataset.warnings,

    quality: {
      status: dataset.quality_mask_available
        ? 'available'
        : 'unavailable',

      summary: dataset.quality_mask_available
        ? 'Quality mask available'
        : null,
    },

    /*
     * The current backend catalogue confirms whether
     * coverage exists, but does not yet return a dedicated
     * frontend compatibility decision/reason.
     *
     * We therefore use coverage_available as the only
     * backend-supported compatibility gate here rather
     * than inventing additional compatibility rules.
     */
    isCompatible: dataset.coverage_available,

    incompatibilityReason:
      dataset.coverage_available
        ? null
        : 'Dataset coverage is unavailable.',
  }
}

export async function getDatasets(): Promise<
  DatasetMetadata[]
> {
  const response = await fetch(
    `${API_BASE_URL}/api/datasets`,
  )

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  const datasets =
    (await response.json()) as DatasetResponse[]

  return datasets.map(mapDatasetResponse)
}

export async function uploadDataset(
  input: DatasetUploadInput,
): Promise<DatasetMetadata> {
  const formData = new FormData()

  formData.append('file', input.file)
  formData.append('display_name', input.displayName)

  formData.append(
    'metadata_json',
    JSON.stringify({
      acquisition_date: input.acquisitionDate,
      capabilities: input.capabilities,
      water_methods: input.waterMethods,
    }),
  )

  const response = await fetch(
    `${API_BASE_URL}/api/datasets/upload`,
    {
      method: 'POST',
      body: formData,
    },
  )

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  const dataset =
    (await response.json()) as DatasetResponse

  return mapDatasetResponse(dataset)
}
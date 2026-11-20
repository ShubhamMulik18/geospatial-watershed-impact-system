import { getAuthHeaders } from './authApi'

export type PredictionResponse = {
  prediction_id: string
  photo_id: string
  class_id: string
  predicted_class: string
  confidence: number
  requires_verification: boolean
  model_version: string
  warnings?: string[]
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
  'http://127.0.0.1:8000'

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
    // The backend did not return a JSON error body.
  }

  return `Prediction request failed with status ${response.status}.`
}

export async function createPrediction(
  photoId: string,
): Promise<PredictionResponse> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  }

  const response = await fetch(
    `${API_BASE_URL}/api/photos/${encodeURIComponent(photoId)}/prediction`,
    {
      method: 'POST',
      headers,
      credentials: 'include',
    },
  )

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as PredictionResponse
}

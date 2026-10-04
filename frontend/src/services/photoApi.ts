export type PhotoUploadResponse = {
  photo_id: string
  latitude: number | null
  longitude: number | null
  capture_date: string | null
  exif_status: 'available' | 'partial' | 'missing' | 'invalid'
  warnings: string[]
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
    // The backend did not return a JSON error body.
  }

  return `Photo upload failed with status ${response.status}.`
}

export async function uploadPhoto(
  file: File,
): Promise<PhotoUploadResponse> {
  const formData = new FormData()

  formData.append('file', file)

  const response = await fetch(
    `${API_BASE_URL}/api/photos/upload`,
    {
      method: 'POST',
      body: formData,
    },
  )

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as PhotoUploadResponse
}
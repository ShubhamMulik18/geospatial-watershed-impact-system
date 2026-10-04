import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { uploadPhoto } from './photoApi'

describe('photoApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('uploads a photo and returns backend metadata', async () => {
    const backendResponse = {
      photo_id: 'photo-123',
      latitude: 16.95,
      longitude: 73.55,
      capture_date: '2026-10-04',
      exif_status: 'available',
      warnings: [],
    }

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify(backendResponse), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
        }),
      )

    const file = new File(
      ['test-image'],
      'watershed.jpg',
      {
        type: 'image/jpeg',
      },
    )

    const result = await uploadPhoto(file)

    expect(result).toEqual(backendResponse)

    expect(fetchMock).toHaveBeenCalledOnce()

    const [url, options] = fetchMock.mock.calls[0]

    expect(url).toBe(
      'http://localhost:8000/api/photos/upload',
    )

    expect(options?.method).toBe('POST')
    expect(options?.body).toBeInstanceOf(FormData)

    const formData = options?.body as FormData

    expect(formData.get('file')).toBe(file)
  })

  it('preserves missing EXIF metadata from the backend', async () => {
    const backendResponse = {
      photo_id: 'photo-456',
      latitude: null,
      longitude: null,
      capture_date: null,
      exif_status: 'missing',
      warnings: ['GPS metadata is unavailable.'],
    }

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(backendResponse), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }),
    )

    const file = new File(
      ['test-image'],
      'without-exif.jpg',
      {
        type: 'image/jpeg',
      },
    )

    const result = await uploadPhoto(file)

    expect(result.latitude).toBeNull()
    expect(result.longitude).toBeNull()
    expect(result.capture_date).toBeNull()
    expect(result.exif_status).toBe('missing')
    expect(result.warnings).toEqual([
      'GPS metadata is unavailable.',
    ])
  })

  it('uses the backend error envelope message when upload fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'photo_upload_failed',
            message: 'Unable to process uploaded photo.',
          },
        }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    )

    const file = new File(
      ['invalid-image'],
      'invalid.jpg',
      {
        type: 'image/jpeg',
      },
    )

    await expect(uploadPhoto(file)).rejects.toThrow(
      'Unable to process uploaded photo.',
    )
  })

  it('uses FastAPI detail errors when provided', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: 'Unsupported image format.',
        }),
        {
          status: 422,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    )

    const file = new File(
      ['invalid-image'],
      'invalid.jpg',
      {
        type: 'image/jpeg',
      },
    )

    await expect(uploadPhoto(file)).rejects.toThrow(
      'Unsupported image format.',
    )
  })
})
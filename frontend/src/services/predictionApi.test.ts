import { afterEach, describe, expect, it, vi } from 'vitest'
import { createPrediction } from './predictionApi'

describe('predictionApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('submits photo for AI prediction and returns response', async () => {
    const mockPrediction = {
      prediction_id: 'pred-101',
      photo_id: 'photo-101',
      class: 'Check Dam',
      confidence: 0.94,
      model_version: 'mobilenetv2_v1',
      inference_time_ms: 45.2,
      bounding_box: null,
      notes: 'Predicted intervention',
    }

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockPrediction), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const result = await createPrediction('photo-101')

    expect(result).toEqual(mockPrediction)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/photos/photo-101/prediction',
      expect.objectContaining({
        method: 'POST',
      }),
    )
  })

  it('throws error when server responds with 400', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Photo not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(createPrediction('missing-photo')).rejects.toThrow(
      'Photo not found',
    )
  })
})

import { useEffect, useState } from 'react'
import { ImageOverlay } from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

import type { RasterResultLayer } from '../../types/analysisResult'
import { getAuthHeaders, getAuthToken } from '../../services/authApi'

type RasterOverlayProps = {
  layer: RasterResultLayer
  opacity: number
  visible: boolean
}

function RasterOverlay({
  layer,
  opacity,
  visible,
}: RasterOverlayProps) {
  const [resolvedUrl, setResolvedUrl] = useState<string | null>(null)

  useEffect(() => {
    let isCancelled = false
    let objectUrlToRevoke: string | null = null

    if (!layer.preview_url) {
      setResolvedUrl(null)
      return
    }

    const token = getAuthToken()
    let requestUrl = layer.preview_url
    if (token && !requestUrl.includes('token=')) {
      const sep = requestUrl.includes('?') ? '&' : '?'
      requestUrl = `${requestUrl}${sep}token=${encodeURIComponent(token)}`
    }

    fetch(requestUrl, {
      headers: getAuthHeaders(),
      credentials: 'include',
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load raster image: ${response.status}`)
        }
        const blob = await response.blob()
        if (!isCancelled) {
          if (typeof URL.createObjectURL === 'function') {
            objectUrlToRevoke = URL.createObjectURL(blob)
            setResolvedUrl(objectUrlToRevoke)
          } else {
            setResolvedUrl(requestUrl)
          }
        }
      })
      .catch((error) => {
        console.warn('Falling back to direct raster overlay URL:', error)
        if (!isCancelled) {
          setResolvedUrl(requestUrl)
        }
      })

    return () => {
      isCancelled = true
      if (objectUrlToRevoke && typeof URL.revokeObjectURL === 'function') {
        URL.revokeObjectURL(objectUrlToRevoke)
      }
    }
  }, [layer.preview_url])

  if (!visible || !resolvedUrl) {
    return null
  }

  const [left, bottom, right, top] = layer.bounds_wgs84

  const bounds: LatLngBoundsExpression = [
    [bottom, left],
    [top, right],
  ]

  return (
    <ImageOverlay
      url={resolvedUrl}
      bounds={bounds}
      opacity={opacity}
      interactive={false}
    />
  )
}

export default RasterOverlay

import { ImageOverlay } from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

import type { RasterResultLayer } from '../../types/analysisResult'

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
  if (!visible || layer.preview_url === null) {
    return null
  }

  const [left, bottom, right, top] = layer.bounds_wgs84

  const bounds: LatLngBoundsExpression = [
    [bottom, left],
    [top, right],
  ]

  return (
    <ImageOverlay
      url={layer.preview_url}
      bounds={bounds}
      opacity={opacity}
      interactive={false}
    />
  )
}

export default RasterOverlay
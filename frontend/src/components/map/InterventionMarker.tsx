import { Marker, Popup } from 'react-leaflet'

import type { GeoJsonPosition } from '../../utils/coordinates'
import { geoJsonToLeaflet } from '../../utils/coordinates'

type InterventionMarkerProps = {
  location: GeoJsonPosition
  label?: string
}

function InterventionMarker({
  location,
  label = 'Field photo location',
}: InterventionMarkerProps) {
  const markerPosition = geoJsonToLeaflet(location)

  return (
    <Marker position={markerPosition}>
      <Popup>{label}</Popup>
    </Marker>
  )
}

export default InterventionMarker
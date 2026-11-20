import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import { Polygon } from 'leaflet'
import type { Layer, LatLng } from 'leaflet'
import '@geoman-io/leaflet-geoman-free'

import {
  leafletToGeoJson,
  type GeoJsonPosition,
} from '../../utils/coordinates'

export type StudyAreaPolygon = {
  type: 'Polygon'
  coordinates: GeoJsonPosition[][]
}

type PolygonEditorProps = {
  polygon: StudyAreaPolygon | null
  onPolygonChange: (
    polygon: StudyAreaPolygon | null,
  ) => void
}

function layerToStudyAreaPolygon(
  layer: Layer,
): StudyAreaPolygon | null {
  if (!(layer instanceof Polygon)) {
    return null
  }

  const latLngs = layer.getLatLngs()

  if (
    !Array.isArray(latLngs) ||
    latLngs.length === 0
  ) {
    return null
  }

  const firstRing = latLngs[0]

  if (
    !Array.isArray(firstRing) ||
    firstRing.length < 3
  ) {
    return null
  }

  const coordinates: GeoJsonPosition[] = (
    firstRing as LatLng[]
  ).map((latLng) =>
    leafletToGeoJson([
      latLng.lat,
      latLng.lng,
    ]),
  )

  const firstPosition = coordinates[0]
  const lastPosition =
    coordinates[coordinates.length - 1]

  if (
    firstPosition[0] !== lastPosition[0] ||
    firstPosition[1] !== lastPosition[1]
  ) {
    coordinates.push([...firstPosition])
  }

  return {
    type: 'Polygon',
    coordinates: [coordinates],
  }
}

function PolygonEditor({
  polygon,
  onPolygonChange,
}: PolygonEditorProps) {
  const map = useMap()

  const activePolygonRef =
    useRef<Layer | null>(null)

  const onPolygonChangeRef =
    useRef(onPolygonChange)

  useEffect(() => {
    onPolygonChangeRef.current =
      onPolygonChange
  }, [onPolygonChange])

  /*
   * Synchronize the Leaflet layer with React/context state.
   *
   * If the polygon is cleared by an external action such
   * as removing or replacing the photo, the visible
   * Leaflet polygon must also be removed.
   */
  useEffect(() => {
    if (
      polygon === null &&
      activePolygonRef.current !== null
    ) {
      const layer = activePolygonRef.current

      activePolygonRef.current = null

      if (map.hasLayer(layer)) {
        map.removeLayer(layer)
      }
    }
  }, [map, polygon])

  useEffect(() => {
    map.pm.addControls({
      position: 'topleft',

      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: false,

      drawPolygon: true,

      drawCircle: false,
      drawText: false,

      editMode: true,
      dragMode: false,
      cutPolygon: false,
      removalMode: true,
      rotateMode: false,
    })

    function updatePolygon(layer: Layer) {
      const updatedPolygon =
        layerToStudyAreaPolygon(layer)

      if (updatedPolygon) {
        onPolygonChangeRef.current(
          updatedPolygon,
        )
      }
    }

    function attachPolygonListeners(
      layer: Layer,
    ) {
      layer.on('pm:edit', () => {
        updatePolygon(layer)
      })

      layer.on('pm:vertexadded', () => {
        updatePolygon(layer)
      })

      layer.on('pm:vertexremoved', () => {
        updatePolygon(layer)
      })

      layer.on('pm:markerdragend', () => {
        updatePolygon(layer)
      })
    }

    function handleCreate(event: {
      layer: Layer
      shape: string
    }) {
      if (event.shape !== 'Polygon') {
        return
      }

      if (activePolygonRef.current) {
        map.removeLayer(event.layer)
        map.pm.disableDraw()
        return
      }

      const createdPolygon =
        layerToStudyAreaPolygon(event.layer)

      if (!createdPolygon) {
        map.removeLayer(event.layer)
        return
      }

      activePolygonRef.current =
        event.layer

      attachPolygonListeners(
        event.layer,
      )

      onPolygonChangeRef.current(
        createdPolygon,
      )

      map.pm.disableDraw()
    }

    function handleDrawStart(event: {
      shape: string
    }) {
      if (
        event.shape === 'Polygon' &&
        activePolygonRef.current
      ) {
        map.pm.disableDraw()
      }
    }

    function handleRemove(event: {
      layer: Layer
    }) {
      if (
        event.layer !==
        activePolygonRef.current
      ) {
        return
      }

      activePolygonRef.current = null

      onPolygonChangeRef.current(null)
    }

    map.on(
      'pm:create',
      handleCreate,
    )

    map.on(
      'pm:drawstart',
      handleDrawStart,
    )

    map.on(
      'pm:remove',
      handleRemove,
    )

    return () => {
      map.off(
        'pm:create',
        handleCreate,
      )

      map.off(
        'pm:drawstart',
        handleDrawStart,
      )

      map.off(
        'pm:remove',
        handleRemove,
      )

      map.pm.disableDraw()
      map.pm.removeControls()
    }
  }, [map])

  return null
}

export default PolygonEditor
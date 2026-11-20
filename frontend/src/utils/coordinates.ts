export type GeoJsonPosition = [longitude: number, latitude: number]

export type LeafletPosition = [latitude: number, longitude: number]

export function geoJsonToLeaflet(
  position: GeoJsonPosition,
): LeafletPosition {
  const [longitude, latitude] = position

  return [latitude, longitude]
}

export function leafletToGeoJson(
  position: LeafletPosition,
): GeoJsonPosition {
  const [latitude, longitude] = position

  return [longitude, latitude]
}
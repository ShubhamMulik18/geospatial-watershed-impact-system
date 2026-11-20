import type { GeoJsonPosition } from './coordinates'

export type PolygonValidationResult = {
  isValid: boolean
  errors: string[]
}

function positionsEqual(
  first: GeoJsonPosition,
  second: GeoJsonPosition,
) {
  return first[0] === second[0] && first[1] === second[1]
}

function orientation(
  first: GeoJsonPosition,
  second: GeoJsonPosition,
  third: GeoJsonPosition,
) {
  const value =
    (second[1] - first[1]) * (third[0] - second[0]) -
    (second[0] - first[0]) * (third[1] - second[1])

  if (Math.abs(value) < Number.EPSILON) {
    return 0
  }

  return value > 0 ? 1 : 2
}

function pointOnSegment(
  first: GeoJsonPosition,
  point: GeoJsonPosition,
  second: GeoJsonPosition,
) {
  return (
    point[0] <= Math.max(first[0], second[0]) &&
    point[0] >= Math.min(first[0], second[0]) &&
    point[1] <= Math.max(first[1], second[1]) &&
    point[1] >= Math.min(first[1], second[1])
  )
}

function segmentsIntersect(
  firstStart: GeoJsonPosition,
  firstEnd: GeoJsonPosition,
  secondStart: GeoJsonPosition,
  secondEnd: GeoJsonPosition,
) {
  const orientation1 = orientation(
    firstStart,
    firstEnd,
    secondStart,
  )

  const orientation2 = orientation(
    firstStart,
    firstEnd,
    secondEnd,
  )

  const orientation3 = orientation(
    secondStart,
    secondEnd,
    firstStart,
  )

  const orientation4 = orientation(
    secondStart,
    secondEnd,
    firstEnd,
  )

  if (
    orientation1 !== orientation2 &&
    orientation3 !== orientation4
  ) {
    return true
  }

  if (
    orientation1 === 0 &&
    pointOnSegment(firstStart, secondStart, firstEnd)
  ) {
    return true
  }

  if (
    orientation2 === 0 &&
    pointOnSegment(firstStart, secondEnd, firstEnd)
  ) {
    return true
  }

  if (
    orientation3 === 0 &&
    pointOnSegment(secondStart, firstStart, secondEnd)
  ) {
    return true
  }

  if (
    orientation4 === 0 &&
    pointOnSegment(secondStart, firstEnd, secondEnd)
  ) {
    return true
  }

  return false
}

function hasSelfIntersection(
  ring: GeoJsonPosition[],
) {
  const segmentCount = ring.length - 1

  for (let firstIndex = 0; firstIndex < segmentCount; firstIndex += 1) {
    const firstStart = ring[firstIndex]
    const firstEnd = ring[firstIndex + 1]

    for (
      let secondIndex = firstIndex + 1;
      secondIndex < segmentCount;
      secondIndex += 1
    ) {
      const secondStart = ring[secondIndex]
      const secondEnd = ring[secondIndex + 1]

      const segmentsAreAdjacent =
        secondIndex === firstIndex + 1 ||
        (firstIndex === 0 && secondIndex === segmentCount - 1)

      if (segmentsAreAdjacent) {
        continue
      }

      if (
        segmentsIntersect(
          firstStart,
          firstEnd,
          secondStart,
          secondEnd,
        )
      ) {
        return true
      }
    }
  }

  return false
}

export function validatePolygonRing(
  ring: GeoJsonPosition[],
): PolygonValidationResult {
  const errors: string[] = []

  if (ring.length < 4) {
    errors.push(
      'A polygon requires at least three vertices and a closed ring.',
    )

    return {
      isValid: false,
      errors,
    }
  }

  const firstPosition = ring[0]
  const lastPosition = ring[ring.length - 1]

  if (!positionsEqual(firstPosition, lastPosition)) {
    errors.push('The polygon ring is not closed.')
  }

  const uniqueVertices = ring.slice(0, -1)

  if (uniqueVertices.length < 3) {
    errors.push('A polygon requires at least three vertices.')
  }

  const hasInvalidCoordinate = ring.some(
    ([longitude, latitude]) =>
      !Number.isFinite(longitude) ||
      !Number.isFinite(latitude) ||
      longitude < -180 ||
      longitude > 180 ||
      latitude < -90 ||
      latitude > 90,
  )

  if (hasInvalidCoordinate) {
    errors.push(
      'The polygon contains invalid longitude or latitude values.',
    )
  }

  if (
    errors.length === 0 &&
    hasSelfIntersection(ring)
  ) {
    errors.push(
      'The polygon cannot contain self-intersecting edges.',
    )
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { DatasetResult, RasterResultLayer } from '../../types/analysisResult'
import RasterResultMap from './RasterResultMap'

// Mock react-leaflet components since jsdom doesn't support canvas/DOM layout
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="leaflet-map-container">{children}</div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  useMap: () => ({ fitBounds: vi.fn() }),
}))

vi.mock('./RasterOverlay', () => ({
  default: () => <div data-testid="raster-overlay" />,
}))

const createMockLayer = (
  layerId: string,
  datasetId: string,
  kind: string = 'ndvi',
): RasterResultLayer => ({
  layer_id: layerId,
  dataset_id: datasetId,
  kind,
  preview_url: `/api/artifacts/analyses/123/layers/${layerId}/preview.png`,
  download_url: `/api/artifacts/analyses/123/layers/${layerId}/raster.tif`,
  bounds_wgs84: [74.2, 16.6, 74.3, 16.7],
  preview_crs: 'EPSG:4326',
  legend: {
    'Min NDVI': 0.1,
    'Max NDVI': 0.8,
  },
})

const dataset2020: DatasetResult = {
  datasetId: 'ds-2020',
  datasetName: 'Sentinel-2 Tile (2020)',
  year: 2020,
  acquisitionDate: '2020-01-15',
  ndvi: 0.35,
  waterArea: 1.2,
}

const dataset2023: DatasetResult = {
  datasetId: 'ds-2023',
  datasetName: 'Sentinel-2 Tile (2023)',
  year: 2023,
  acquisitionDate: '2023-01-18',
  ndvi: 0.42,
  waterArea: 1.5,
}

const dataset2026: DatasetResult = {
  datasetId: 'ds-2026',
  datasetName: 'Sentinel-2 Tile (2026)',
  year: 2026,
  acquisitionDate: '2026-01-20',
  ndvi: 0.51,
  waterArea: 2.1,
}

const dataset2028: DatasetResult = {
  datasetId: 'ds-2028',
  datasetName: 'Sentinel-2 Tile (2028)',
  year: 2028,
  acquisitionDate: '2028-01-22',
  ndvi: 0.58,
  waterArea: 2.5,
}

describe('RasterResultMap', () => {
  it('renders 2 map panels in two-date comparison mode with Earlier/Later tags', () => {
    const layers = [
      createMockLayer('l1', 'ds-2020', 'ndvi'),
      createMockLayer('l2', 'ds-2026', 'ndvi'),
    ]
    const datasetResults = [dataset2020, dataset2026]

    render(<RasterResultMap layers={layers} datasetResults={datasetResults} />)

    expect(screen.getByText('Side-by-Side Comparison')).toBeInTheDocument()
    expect(screen.getByText('Earlier / Baseline')).toBeInTheDocument()
    expect(screen.getByText('Later / Latest')).toBeInTheDocument()

    expect(screen.getByText('Sentinel-2 Tile (2020)')).toBeInTheDocument()
    expect(screen.getByText('Sentinel-2 Tile (2026)')).toBeInTheDocument()
    expect(screen.getByText('Acquisition Date: 2020-01-15')).toBeInTheDocument()
    expect(screen.getByText('Acquisition Date: 2026-01-20')).toBeInTheDocument()
    expect(screen.getByText('Mean NDVI: 0.35')).toBeInTheDocument()
    expect(screen.getByText('Mean NDVI: 0.51')).toBeInTheDocument()

    const downloadLinks = screen.getAllByText('Download GeoTIFF')
    expect(downloadLinks).toHaveLength(2)
  })

  it('renders 3 map panels dynamically in multi-date series mode', () => {
    const layers = [
      createMockLayer('l1', 'ds-2020', 'ndvi'),
      createMockLayer('l2', 'ds-2023', 'ndvi'),
      createMockLayer('l3', 'ds-2026', 'ndvi'),
    ]
    const datasetResults = [dataset2020, dataset2023, dataset2026]

    render(<RasterResultMap layers={layers} datasetResults={datasetResults} />)

    expect(
      screen.getByText('Multi-Date Series (3 Observations)'),
    ).toBeInTheDocument()
    expect(screen.getByText('Baseline (2020)')).toBeInTheDocument()
    expect(screen.getByText('Observation (2023)')).toBeInTheDocument()
    expect(screen.getByText('Latest (2026)')).toBeInTheDocument()

    expect(screen.getByText('Sentinel-2 Tile (2020)')).toBeInTheDocument()
    expect(screen.getByText('Sentinel-2 Tile (2023)')).toBeInTheDocument()
    expect(screen.getByText('Sentinel-2 Tile (2026)')).toBeInTheDocument()

    const downloadLinks = screen.getAllByText('Download GeoTIFF')
    expect(downloadLinks).toHaveLength(3)
  })

  it('renders 4 map panels dynamically for 4 observations', () => {
    const layers = [
      createMockLayer('l1', 'ds-2020', 'ndvi'),
      createMockLayer('l2', 'ds-2023', 'ndvi'),
      createMockLayer('l3', 'ds-2026', 'ndvi'),
      createMockLayer('l4', 'ds-2028', 'ndvi'),
    ]
    const datasetResults = [dataset2020, dataset2023, dataset2026, dataset2028]

    render(<RasterResultMap layers={layers} datasetResults={datasetResults} />)

    expect(
      screen.getByText('Multi-Date Series (4 Observations)'),
    ).toBeInTheDocument()
    expect(screen.getByText('Baseline (2020)')).toBeInTheDocument()
    expect(screen.getByText('Observation (2023)')).toBeInTheDocument()
    expect(screen.getByText('Observation (2026)')).toBeInTheDocument()
    expect(screen.getByText('Latest (2028)')).toBeInTheDocument()

    const downloadLinks = screen.getAllByText('Download GeoTIFF')
    expect(downloadLinks).toHaveLength(4)
  })

  it('sorts panels chronologically earliest to latest regardless of input order', () => {
    const layers = [
      createMockLayer('l3', 'ds-2026', 'ndvi'),
      createMockLayer('l1', 'ds-2020', 'ndvi'),
      createMockLayer('l2', 'ds-2023', 'ndvi'),
    ]
    // Provide in unordered sequence
    const datasetResults = [dataset2026, dataset2020, dataset2023]

    const { container } = render(
      <RasterResultMap layers={layers} datasetResults={datasetResults} />,
    )

    const titles = Array.from(
      container.querySelectorAll('span.text-sm.font-semibold.text-white'),
    ).map((el) => el.textContent)

    expect(titles).toEqual([
      'Sentinel-2 Tile (2020)',
      'Sentinel-2 Tile (2023)',
      'Sentinel-2 Tile (2026)',
    ])
  })

  it('handles missing observation layer with a clear unavailable message', () => {
    // Only 2020 and 2026 have layers; 2023 has no matching layer
    const layers = [
      createMockLayer('l1', 'ds-2020', 'ndvi'),
      createMockLayer('l3', 'ds-2026', 'ndvi'),
    ]
    const datasetResults = [dataset2020, dataset2023, dataset2026]

    render(<RasterResultMap layers={layers} datasetResults={datasetResults} />)

    expect(
      screen.getByText('No displayable raster layer available for this observation.'),
    ).toBeInTheDocument()

    // 2 download links available (for 2020 and 2026)
    const downloadLinks = screen.getAllByText('Download GeoTIFF')
    expect(downloadLinks).toHaveLength(2)
  })

  it('renders unavailable state when layers array is completely empty', () => {
    render(<RasterResultMap layers={[]} datasetResults={[dataset2020]} />)

    expect(screen.getByText('Result Layers Unavailable')).toBeInTheDocument()
  })
})


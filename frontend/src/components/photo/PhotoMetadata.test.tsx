import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import PhotoMetadata from './PhotoMetadata'

describe('PhotoMetadata', () => {
  it('renders latitude, longitude, and capture date cleanly', () => {
    render(
      <PhotoMetadata
        metadata={{
          latitude: 16.670308,
          longitude: 74.231602,
          capturedAt: '2026-11-18',
          exifStatus: 'missing',
          warnings: [
            'GPS location extracted from photo text stamp via OCR (EXIF GPS unavailable).',
            'Capture date extracted from photo text stamp via OCR (EXIF date unavailable).',
          ],
        }}
      />,
    )

    // Verify useful extracted metadata is displayed
    expect(screen.getByText('Latitude')).toBeInTheDocument()
    expect(screen.getByText('16.670308')).toBeInTheDocument()

    expect(screen.getByText('Longitude')).toBeInTheDocument()
    expect(screen.getByText('74.231602')).toBeInTheDocument()

    expect(screen.getByText('Capture Date')).toBeInTheDocument()
    expect(screen.getByText('2026-11-18')).toBeInTheDocument()

    expect(screen.getByText('Location available')).toBeInTheDocument()

    // Verify EXIF Status is NOT rendered
    expect(screen.queryByText('EXIF Status')).not.toBeInTheDocument()
    expect(screen.queryByText('Missing')).not.toBeInTheDocument()
    expect(screen.queryByText('Available')).not.toBeInTheDocument()
    expect(screen.queryByText('Partial')).not.toBeInTheDocument()

    // Verify Metadata warnings section and warning items are NOT rendered
    expect(screen.queryByText('Metadata warnings')).not.toBeInTheDocument()
    expect(
      screen.queryByText(/GPS location extracted from photo text stamp/i),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(/Capture date extracted from photo text stamp/i),
    ).not.toBeInTheDocument()
  })

  it('renders unavailable indicators when coordinates and date are null', () => {
    render(
      <PhotoMetadata
        metadata={{
          latitude: null,
          longitude: null,
          capturedAt: null,
        }}
      />,
    )

    expect(screen.getByText('Location unavailable')).toBeInTheDocument()
    expect(screen.getAllByText('Unavailable')).toHaveLength(3)
    expect(
      screen.getByText(/GPS coordinates are unavailable/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Capture date is unavailable/i),
    ).toBeInTheDocument()

    // Still no EXIF Status or Metadata warnings
    expect(screen.queryByText('EXIF Status')).not.toBeInTheDocument()
    expect(screen.queryByText('Metadata warnings')).not.toBeInTheDocument()
  })
})


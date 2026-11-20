import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import DatasetSelector from './DatasetSelector'
import type { DatasetMetadata } from '../../types/dataset'

const compatibleDataset: DatasetMetadata = {
  id: 'dataset-1',
  displayName: 'Watershed 2025',
  year: 2025,
  acquisitionDate: '2025-01-15',
  coverage: 'Available',
  resolution: '10 m',
  supportedIndicators: [],
  waterMethods: [],
  warnings: [],
  quality: {
    status: 'available',
    summary: null,
  },
  isCompatible: true,
  incompatibilityReason: null,
}

const secondDataset: DatasetMetadata = {
  ...compatibleDataset,
  id: 'dataset-2',
  displayName: 'Watershed 2024',
  year: 2024,
}

const incompatibleDataset: DatasetMetadata = {
  ...compatibleDataset,
  id: 'dataset-3',
  displayName: 'Unsupported Dataset',
  isCompatible: false,
  incompatibilityReason: 'Coverage is unavailable.',
}

describe('DatasetSelector', () => {
  it('shows the empty catalogue state', () => {
    render(
      <DatasetSelector
        datasets={[]}
        selectedDatasetIds={[]}
        onSelectionChange={vi.fn()}
      />,
    )

    expect(
      screen.getByText('No datasets available'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Select at least 2 compatible datasets.'),
    ).toBeInTheDocument()
  })

  it('selects a compatible dataset', async () => {
    const user = userEvent.setup()
    const onSelectionChange = vi.fn()

    render(
      <DatasetSelector
        datasets={[compatibleDataset]}
        selectedDatasetIds={[]}
        onSelectionChange={onSelectionChange}
      />,
    )

    await user.click(
      screen.getByRole('button', {
        name: /Watershed 2025/i,
      }),
    )

    expect(onSelectionChange).toHaveBeenCalledWith([
      'dataset-1',
    ])
  })

  it('deselects an already selected dataset', async () => {
    const user = userEvent.setup()
    const onSelectionChange = vi.fn()

    render(
      <DatasetSelector
        datasets={[compatibleDataset]}
        selectedDatasetIds={['dataset-1']}
        onSelectionChange={onSelectionChange}
      />,
    )

    await user.click(
      screen.getByRole('button', {
        name: /Watershed 2025/i,
      }),
    )

    expect(onSelectionChange).toHaveBeenCalledWith([])
  })

  it('disables incompatible datasets', () => {
    render(
      <DatasetSelector
        datasets={[incompatibleDataset]}
        selectedDatasetIds={[]}
        onSelectionChange={vi.fn()}
      />,
    )

    expect(
      screen.getByRole('button', {
        name: /Unsupported Dataset/i,
      }),
    ).toBeDisabled()

    expect(
      screen.getByText('Coverage is unavailable.'),
    ).toBeInTheDocument()
  })

  it('shows one remaining dataset when one dataset is selected', () => {
    render(
      <DatasetSelector
        datasets={[compatibleDataset, secondDataset]}
        selectedDatasetIds={['dataset-1']}
        onSelectionChange={vi.fn()}
      />,
    )

    expect(
      screen.getByText('1 selected'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Select 1 more compatible dataset.'),
    ).toBeInTheDocument()
  })

  it('shows that the minimum requirement is satisfied with two datasets', () => {
    render(
      <DatasetSelector
        datasets={[compatibleDataset, secondDataset]}
        selectedDatasetIds={['dataset-1', 'dataset-2']}
        onSelectionChange={vi.fn()}
      />,
    )

    expect(
      screen.getByText('2 selected'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Minimum dataset requirement satisfied.'),
    ).toBeInTheDocument()
  })
})
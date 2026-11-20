import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ResultSummary from './ResultSummary'

describe('ResultSummary', () => {
  it('renders the analysis summary values', () => {
    render(
      <ResultSummary
        predictedClass="Check Dam"
        confidence={0.87}
        datasetCount={2}
        indicatorCount={1}
      />,
    )

    expect(screen.getByText('Check Dam')).toBeInTheDocument()

    expect(screen.getByText('Confidence')).toBeInTheDocument()
    expect(screen.getByText('87')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()

    expect(screen.getByText('Datasets')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()

    expect(screen.getByText('Indicators')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('shows unavailable values when prediction data is missing', () => {
    render(
      <ResultSummary
        predictedClass={null}
        confidence={null}
        datasetCount={0}
        indicatorCount={0}
      />,
    )

    expect(screen.getAllByText('Unavailable')).toHaveLength(2)
  })
})
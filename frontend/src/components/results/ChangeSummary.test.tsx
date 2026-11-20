import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ChangeMetric } from '../../types/analysisResult'
import ChangeSummary from './ChangeSummary'

describe('ChangeSummary Direction-Aware Styling', () => {
  it('renders positive change with green badge and plus sign', () => {
    const changes: ChangeMetric[] = [
      {
        id: 'water-change',
        label: 'Surface Water Area',
        before: 0.01,
        after: 0.30,
        change: 0.29,
        unit: 'ha',
      },
    ]

    render(<ChangeSummary changes={changes} />)

    const badge = screen.getByText('+0.29 ha')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('text-emerald-400')
    expect(badge.className).toContain('border-emerald-500/20')
  })

  it('renders negative change with red badge and minus sign', () => {
    const changes: ChangeMetric[] = [
      {
        id: 'water-loss',
        label: 'Surface Water Area',
        before: 0.30,
        after: 0.01,
        change: -0.29,
        unit: 'ha',
      },
    ]

    render(<ChangeSummary changes={changes} />)

    const badge = screen.getByText('-0.29 ha')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('text-rose-400')
    expect(badge.className).toContain('border-rose-500/20')
  })

  it('renders zero change with neutral slate badge', () => {
    const changes: ChangeMetric[] = [
      {
        id: 'ndvi-neutral',
        label: 'Vegetation Index',
        before: 0.35,
        after: 0.35,
        change: 0,
        unit: null,
      },
    ]

    render(<ChangeSummary changes={changes} />)

    const badge = screen.getByText('0')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('text-slate-300')
  })

  it('renders unavailable state when changes array is empty', () => {
    render(<ChangeSummary changes={[]} />)
    expect(screen.getByText('Change measurements are unavailable.')).toBeInTheDocument()
  })
})


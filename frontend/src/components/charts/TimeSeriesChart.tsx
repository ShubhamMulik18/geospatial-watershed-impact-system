import { useMemo } from 'react'
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import type { ScriptableLineSegmentContext } from 'chart.js'
import { Line } from 'react-chartjs-2'

import type { DatasetResult } from '../../types/analysisResult'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
)

type TimeSeriesChartProps = {
  results: DatasetResult[]
  metric: 'ndvi' | 'waterArea'
}

function TimeSeriesChart({
  results,
  metric,
}: TimeSeriesChartProps) {
  const metricLabel =
    metric === 'ndvi' ? 'NDVI' : 'Surface Water Area'

  const unit = metric === 'waterArea' ? 'ha' : null

  // Ensure chronological sorting of observations
  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => {
      const timeA = a.acquisitionDate
        ? new Date(a.acquisitionDate).getTime()
        : (a.year ? a.year * 10000 : 0)
      const timeB = b.acquisitionDate
        ? new Date(b.acquisitionDate).getTime()
        : (b.year ? b.year * 10000 : 0)
      return timeA - timeB
    })
  }, [results])

  const availableResults = useMemo(() => {
    return sortedResults.filter((result) => result[metric] !== null)
  }, [sortedResults, metric])

  if (availableResults.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <h3 className="font-semibold text-white">
          {metricLabel} Time Series
        </h3>

        <p className="mt-3 text-sm text-slate-500">
          Time-series data is unavailable.
        </p>
      </div>
    )
  }

  // Determine direction-aware point colors:
  // Baseline point is neutral slate; subsequent points reflect trend relative to preceding epoch.
  const pointColors = availableResults.map((result, idx) => {
    if (idx === 0) return 'rgb(148, 163, 184)'
    const prevVal = availableResults[idx - 1][metric]
    const curVal = result[metric]
    if (prevVal !== null && curVal !== null) {
      if (curVal > prevVal) return 'rgb(52, 211, 153)' // upward -> green
      if (curVal < prevVal) return 'rgb(244, 63, 94)'  // downward -> red
    }
    return 'rgb(148, 163, 184)' // flat -> neutral slate
  })

  const data = {
    labels: availableResults.map(
      (result) =>
        result.acquisitionDate ??
        (result.year !== null
          ? String(result.year)
          : result.datasetName),
    ),

    datasets: [
      {
        label: metricLabel,
        data: availableResults.map((result) => result[metric]),
        borderColor: 'rgb(52, 211, 153)', // Fallback base color
        pointBackgroundColor: pointColors,
        pointBorderColor: 'rgb(15, 23, 42)',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2.5,
        tension: 0.15,
        segment: {
          // Direction-aware segment coloring:
          // Downward segments are red, upward segments are green, flat segments are neutral.
          borderColor: (ctx: ScriptableLineSegmentContext) => {
            const y0 = ctx.p0?.parsed?.y
            const y1 = ctx.p1?.parsed?.y
            if (typeof y0 === 'number' && typeof y1 === 'number') {
              if (y1 < y0) return 'rgb(244, 63, 94)' // downward -> red (rose-500)
              if (y1 > y0) return 'rgb(52, 211, 153)' // upward -> green (emerald-400)
              return 'rgb(148, 163, 184)' // flat -> neutral slate-400
            }
            return 'rgb(52, 211, 153)'
          },
        },
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,

    interaction: {
      intersect: false,
      mode: 'index' as const,
    },

    plugins: {
      legend: {
        display: false,
      },

      tooltip: {
        callbacks: {
          label: (context: { parsed: { y: number | null } }) => {
            const value = context.parsed.y

            if (value === null) {
              return 'Unavailable'
            }

            return `${metricLabel}: ${value}${
              unit ? ` ${unit}` : ''
            }`
          },
        },
      },
    },

    scales: {
      x: {
        ticks: {
          color: '#94a3b8',
        },
        grid: {
          display: false,
        },
      },

      y: {
        ticks: {
          color: '#94a3b8',
        },
        grid: {
          color: 'rgba(71, 85, 105, 0.25)',
        },
      },
    },
  }

  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Multi-date Time Series
        </p>

        <h3 className="mt-1 text-lg font-semibold text-white">
          {metricLabel}
        </h3>

        <p className="mt-2 text-sm text-slate-500">
          Measurements returned for the selected dataset dates
          {unit ? ` (${unit})` : ''}.
        </p>
      </div>

      <div className="mt-6 h-72">
        <Line data={data} options={options} />
      </div>

      <p className="mt-4 text-xs leading-5 text-slate-500">
        The frontend visualizes returned measurements with direction-aware trend lines (green = increase, red = decrease).
      </p>
    </article>
  )
}

export default TimeSeriesChart

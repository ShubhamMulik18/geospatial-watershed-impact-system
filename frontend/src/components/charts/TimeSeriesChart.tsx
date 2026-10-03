import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
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

  const availableResults = results.filter(
    (result) => result[metric] !== null,
  )

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
        data: availableResults.map(
          (result) => result[metric],
        ),
        borderColor: 'rgb(52, 211, 153)',
        backgroundColor: 'rgba(52, 211, 153, 0.15)',
        pointBackgroundColor: 'rgb(52, 211, 153)',
        pointBorderColor: 'rgb(15, 23, 42)',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2,
        tension: 0.25,
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
        The frontend visualizes returned measurements only. Scientific
        values are not calculated by this chart.
      </p>
    </article>
  )
}

export default TimeSeriesChart
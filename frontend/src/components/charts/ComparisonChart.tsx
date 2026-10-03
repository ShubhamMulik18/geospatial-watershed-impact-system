import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

import type { ChangeMetric } from '../../types/analysisResult'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
)

type ComparisonChartProps = {
  change: ChangeMetric
}

function ComparisonChart({ change }: ComparisonChartProps) {
  const hasBeforeValue = change.before !== null
  const hasAfterValue = change.after !== null

  if (!hasBeforeValue && !hasAfterValue) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <h3 className="font-semibold text-white">{change.label}</h3>

        <p className="mt-3 text-sm text-slate-500">
          Comparison data is unavailable.
        </p>
      </div>
    )
  }

  const data = {
    labels: ['Before', 'After'],
    datasets: [
      {
        label: change.label,
        data: [change.before, change.after],
        backgroundColor: [
          'rgba(148, 163, 184, 0.7)',
          'rgba(52, 211, 153, 0.75)',
        ],
        borderColor: [
          'rgb(148, 163, 184)',
          'rgb(52, 211, 153)',
        ],
        borderWidth: 1,
        borderRadius: 8,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,

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

            return `${value}${change.unit ? ` ${change.unit}` : ''}`
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
        beginAtZero: true,
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
          Before vs After
        </p>

        <h3 className="mt-1 text-lg font-semibold text-white">
          {change.label}
        </h3>

        <p className="mt-2 text-sm text-slate-500">
          Returned comparison measurements
          {change.unit ? ` (${change.unit})` : ''}.
        </p>
      </div>

      <div className="mt-6 h-64">
        <Bar data={data} options={options} />
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg bg-slate-950/50 p-3">
          <p className="text-xs text-slate-500">Before</p>
          <p className="mt-1 font-semibold text-slate-200">
            {change.before !== null
              ? `${change.before}${change.unit ? ` ${change.unit}` : ''}`
              : 'Unavailable'}
          </p>
        </div>

        <div className="rounded-lg bg-slate-950/50 p-3">
          <p className="text-xs text-slate-500">After</p>
          <p className="mt-1 font-semibold text-slate-200">
            {change.after !== null
              ? `${change.after}${change.unit ? ` ${change.unit}` : ''}`
              : 'Unavailable'}
          </p>
        </div>

        <div className="rounded-lg bg-slate-950/50 p-3">
          <p className="text-xs text-slate-500">Change</p>
          <p className="mt-1 font-semibold text-emerald-300">
            {change.change !== null
              ? `${change.change}${change.unit ? ` ${change.unit}` : ''}`
              : 'Unavailable'}
          </p>
        </div>
      </div>
    </article>
  )
}

export default ComparisonChart
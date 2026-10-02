import { Link } from 'react-router-dom'

type AnalysisStatus = 'Completed' | 'Processing' | 'Failed'

type AnalysisRecord = {
  id: string
  name: string
  status: AnalysisStatus
  createdAt: string
}

const mockAnalyses: AnalysisRecord[] = [
  {
    id: 'WS-1042',
    name: 'Upper Wardha Watershed',
    status: 'Completed',
    createdAt: '02 Oct 2026, 10:42 AM',
  },
  {
    id: 'WS-1041',
    name: 'Wainganga Catchment Study',
    status: 'Processing',
    createdAt: '01 Oct 2026, 04:18 PM',
  },
  {
    id: 'WS-1040',
    name: 'Kanhan River Assessment',
    status: 'Completed',
    createdAt: '30 Sep 2026, 02:35 PM',
  },
  {
    id: 'WS-1039',
    name: 'Pench Watershed Study',
    status: 'Failed',
    createdAt: '29 Sep 2026, 11:20 AM',
  },
]

const statusStyles: Record<AnalysisStatus, string> = {
  Completed:
    'border-emerald-500/20 bg-emerald-500/10 text-emerald-300',
  Processing:
    'border-amber-500/20 bg-amber-500/10 text-amber-300',
  Failed:
    'border-rose-500/20 bg-rose-500/10 text-rose-300',
}

function RecentAnalyses() {
  return (
    <section
      aria-labelledby="recent-analyses-title"
      className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70"
    >
      <div className="flex flex-col gap-3 border-b border-slate-800 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2
              id="recent-analyses-title"
              className="text-lg font-semibold text-white"
            >
              Recent Analyses
            </h2>

            <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-300">
              Demo data
            </span>
          </div>

          <p className="mt-1 text-sm text-slate-500">
            Recent watershed analysis activity.
          </p>
        </div>

        <Link
          to="/new-analysis"
          className="text-sm font-semibold text-emerald-400 transition hover:text-emerald-300"
        >
          New analysis →
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left">
          <thead className="border-b border-slate-800 bg-slate-950/40">
            <tr>
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Analysis
              </th>

              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                ID
              </th>

              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Status
              </th>

              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Created
              </th>

              <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">
                Action
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800">
            {mockAnalyses.map((analysis) => (
              <tr
                key={analysis.id}
                className="transition hover:bg-slate-800/30"
              >
                <td className="px-6 py-4">
                  <p className="font-medium text-slate-200">
                    {analysis.name}
                  </p>
                </td>

                <td className="px-6 py-4">
                  <span className="font-mono text-sm text-slate-400">
                    {analysis.id}
                  </span>
                </td>

                <td className="px-6 py-4">
                  <span
                    className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusStyles[analysis.status]}`}
                  >
                    {analysis.status}
                  </span>
                </td>

                <td className="px-6 py-4 text-sm text-slate-400">
                  {analysis.createdAt}
                </td>

                <td className="px-6 py-4 text-right">
                  <Link
                    to={`/analyses/${analysis.id}`}
                    className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-400 transition hover:text-emerald-300"
                  >
                    View

                    <svg
                      viewBox="0 0 24 24"
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="m9 18 6-6-6-6"
                      />
                    </svg>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-800 px-6 py-4">
        <p className="text-xs text-slate-500">
          Showing 4 demo analyses
        </p>

        <p className="text-xs text-slate-600">
          Pagination will activate when required by real data.
        </p>
      </div>
    </section>
  )
}

export default RecentAnalyses
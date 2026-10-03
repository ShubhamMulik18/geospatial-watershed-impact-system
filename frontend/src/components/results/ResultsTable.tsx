import type { DatasetResult } from '../../types/analysisResult'

type ResultsTableProps = {
  results: DatasetResult[]
}

function formatValue(
  value: number | null,
  unit?: string,
) {
  if (value === null) {
    return 'Unavailable'
  }

  return unit ? `${value} ${unit}` : value
}

function ResultsTable({ results }: ResultsTableProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          Dataset Results
        </p>

        <h2 className="mt-1 text-xl font-semibold text-white">
          Scientific Measurements
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          Measurements associated with each dataset used in the
          completed analysis.
        </p>
      </div>

      {results.length > 0 ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3 font-semibold">
                  Dataset
                </th>

                <th className="px-4 py-3 font-semibold">
                  Year
                </th>

                <th className="px-4 py-3 font-semibold">
                  Acquisition
                </th>

                <th className="px-4 py-3 font-semibold">
                  NDVI
                </th>

                <th className="px-4 py-3 font-semibold">
                  Water Area
                </th>
              </tr>
            </thead>

            <tbody>
              {results.map((result) => (
                <tr
                  key={result.datasetId}
                  className="border-b border-slate-800/70 last:border-0"
                >
                  <td className="px-4 py-4 font-medium text-slate-200">
                    {result.datasetName}
                  </td>

                  <td className="px-4 py-4 text-slate-400">
                    {result.year ?? 'Unavailable'}
                  </td>

                  <td className="px-4 py-4 text-slate-400">
                    {result.acquisitionDate ?? 'Unavailable'}
                  </td>

                  <td className="px-4 py-4 font-medium text-slate-200">
                    {formatValue(result.ndvi)}
                  </td>

                  <td className="px-4 py-4 font-medium text-slate-200">
                    {formatValue(result.waterArea, 'ha')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-slate-950/30 p-5">
          <p className="text-sm text-slate-500">
            Dataset result measurements are unavailable.
          </p>
        </div>
      )}
    </section>
  )
}

export default ResultsTable
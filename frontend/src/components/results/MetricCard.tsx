type MetricCardProps = {
  label: string
  value: number | null
  unit?: string | null
  description?: string | null
}

function MetricCard({
  label,
  value,
  unit = null,
  description = null,
}: MetricCardProps) {
  const hasValue = value !== null

  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        {label}
      </p>

      <div className="mt-3 flex items-end gap-2">
        <p
          className={`text-2xl font-bold ${
            hasValue
              ? 'text-white'
              : 'text-slate-500'
          }`}
        >
          {hasValue ? value : 'Unavailable'}
        </p>

        {hasValue && unit && (
          <span className="pb-0.5 text-sm font-medium text-slate-400">
            {unit}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-3 text-sm leading-6 text-slate-500">
          {description}
        </p>
      )}
    </article>
  )
}

export default MetricCard
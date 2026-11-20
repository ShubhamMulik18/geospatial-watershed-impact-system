type ValidationErrorsProps = {
  errors: string[]
}

function ValidationErrors({
  errors,
}: ValidationErrorsProps) {
  if (errors.length === 0) {
    return null
  }

  return (
    <section className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-500/10 text-red-300">
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v4m0 4h.01M10.3 4.5 3.6 16.1A2 2 0 0 0 5.3 19h13.4a2 2 0 0 0 1.7-2.9L13.7 4.5a2 2 0 0 0-3.4 0Z"
            />
          </svg>
        </div>

        <div className="min-w-0">
          <p className="font-semibold text-red-200">
            Validation required
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-400">
            Resolve the following issues before starting the
            analysis.
          </p>

          <ul className="mt-4 space-y-2">
            {errors.map((error, index) => (
              <li
                key={`${error}-${index}`}
                className="flex items-start gap-2 text-sm text-red-200"
              >
                <span
                  className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400"
                  aria-hidden="true"
                />

                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

export default ValidationErrors
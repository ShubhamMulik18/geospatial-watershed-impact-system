import React, { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

export default function LoginPage() {
  const { isAuthenticated, isLoading: isAuthLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Determine redirection destination
  const fromLocation =
    (location.state as { from?: { pathname: string } })?.from?.pathname ||
    '/dashboard'

  // If already authenticated and not loading, redirect to target page or dashboard
  if (isAuthenticated && !isAuthLoading) {
    return <Navigate to={fromLocation} replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    const trimmedUsername = username.trim()
    if (!trimmedUsername) {
      setErrorMessage('Please enter your username.')
      return
    }

    if (!password) {
      setErrorMessage('Please enter your password.')
      return
    }

    setIsSubmitting(true)
    try {
      await login(trimmedUsername, password)
      navigate(fromLocation, { replace: true })
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage('Authentication failed. Please check your credentials.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8">
      {/* Background ambient gradient */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-emerald-600/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-cyan-600/10 blur-3xl" />
      </div>

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        {/* Branding */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10 shadow-lg shadow-emerald-500/10">
            <svg
              className="h-8 w-8 text-emerald-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>

          <h2 className="mt-5 text-xs font-semibold uppercase tracking-[0.25em] text-emerald-400">
            Watershed Intelligence
          </h2>

          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Geospatial Analysis Workspace
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Sign in to access satellite monitoring and environmental analysis
          </p>
        </div>

        {/* Card */}
        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl backdrop-blur-md sm:p-8">
          {errorMessage && (
            <div
              role="alert"
              className="mb-6 flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-950/40 p-4 text-rose-300"
            >
              <svg
                className="mt-0.5 h-5 w-5 shrink-0 text-rose-400"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1 text-sm leading-5">
                <p className="font-semibold text-rose-200">Authentication Failed</p>
                <p className="mt-0.5 text-rose-300/90">{errorMessage}</p>
              </div>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="text-rose-400 hover:text-rose-200"
                aria-label="Dismiss error"
              >
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label
                htmlFor="username"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-300"
              >
                Username
              </label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <svg
                    className="h-5 w-5 text-slate-500"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
                  </svg>
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  className="block w-full rounded-xl border border-slate-700 bg-slate-950/70 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 transition focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-300"
              >
                Password
              </label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <svg
                    className="h-5 w-5 text-slate-500"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full rounded-xl border border-slate-700 bg-slate-950/70 py-2.5 pr-11 pl-10 text-sm text-white placeholder-slate-500 transition focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-slate-200"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className={`mt-2 flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-bold tracking-wide transition shadow-lg ${
                isSubmitting
                  ? 'cursor-wait bg-emerald-600/70 text-slate-900 shadow-none'
                  : 'bg-emerald-500 text-slate-950 shadow-emerald-500/20 hover:bg-emerald-400 hover:shadow-emerald-500/30'
              }`}
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="mr-2 h-4 w-4 animate-spin text-slate-950"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          <div className="mt-6 border-t border-slate-800 pt-4 text-center">
            <p className="text-xs text-slate-500">
              Authorized Personnel Only • End-to-End Encrypted Session
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}


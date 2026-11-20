import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'

interface ProtectedRouteProps {
  children?: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div
        data-testid="auth-loading"
        className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-4 text-center"
      >
        <div className="relative flex h-16 w-16 items-center justify-center">
          <div className="absolute h-full w-full animate-ping rounded-full bg-emerald-500/20 duration-1000" />
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
        </div>
        <p className="mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Watershed Security
        </p>
        <p className="mt-1 text-sm text-slate-400">
          Verifying authenticated session...
        </p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children ? <>{children}</> : <Outlet />
}


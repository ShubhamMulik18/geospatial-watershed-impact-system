import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import ProtectedRoute from './ProtectedRoute'
import { AuthContext, type AuthContextType } from '../../context/AuthContext'

describe('ProtectedRoute', () => {
  const renderWithAuth = (authOverrides: Partial<AuthContextType>, initialRoute = '/protected') => {
    const authValue: AuthContextType = {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: async () => {},
      logout: async () => {},
      ...authOverrides,
    }

    return render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={[initialRoute]}>
          <Routes>
            <Route path="/login" element={<div>Login Page Target</div>} />
            <Route element={<ProtectedRoute />}>
              <Route path="/protected" element={<div>Protected Content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )
  }

  it('renders loading state when authentication is being verified', () => {
    renderWithAuth({ isLoading: true, isAuthenticated: false })

    expect(screen.getByTestId('auth-loading')).toBeInTheDocument()
    expect(screen.getByText(/Verifying authenticated session/i)).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(screen.queryByText('Login Page Target')).not.toBeInTheDocument()
  })

  it('redirects unauthenticated users to the login route', () => {
    renderWithAuth({ isLoading: false, isAuthenticated: false })

    expect(screen.getByText('Login Page Target')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders the protected content when authenticated', () => {
    renderWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: {
        id: 'user-1',
        username: 'admin',
        is_active: true,
        created_at: '2026-01-01',
      },
    })

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Login Page Target')).not.toBeInTheDocument()
  })
})


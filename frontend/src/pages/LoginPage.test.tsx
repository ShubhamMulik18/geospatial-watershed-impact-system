import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import { AuthContext, type AuthContextType } from '../context/AuthContext'

describe('LoginPage', () => {
  const mockLogin = vi.fn()
  const mockLogout = vi.fn()

  const defaultAuthValue: AuthContextType = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: mockLogin,
    logout: mockLogout,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderLoginPage = (authOverrides = {}, initialRoute = '/login') => {
    const authValue = { ...defaultAuthValue, ...authOverrides }
    return render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={[initialRoute]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<div>Dashboard Destination</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )
  }

  it('renders username, password input, show password button and sign in button', () => {
    renderLoginPage()

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /show password/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('toggles password visibility when the toggle button is clicked', () => {
    renderLoginPage()

    const passwordInput = screen.getByLabelText(/^password/i)
    const toggleButton = screen.getByRole('button', { name: /show password/i })

    expect(passwordInput).toHaveAttribute('type', 'password')

    fireEvent.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('validates empty inputs and displays error message before submission', async () => {
    renderLoginPage()

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    fireEvent.click(submitButton)

    expect(await screen.findByText('Please enter your username.')).toBeInTheDocument()
    expect(mockLogin).not.toHaveBeenCalled()

    // Fill username only
    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    })
    fireEvent.click(submitButton)

    expect(await screen.findByText('Please enter your password.')).toBeInTheDocument()
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('submits valid credentials and calls login service', async () => {
    mockLogin.mockResolvedValueOnce(undefined)
    renderLoginPage()

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    })
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: 'ValidPassword123!' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin', 'ValidPassword123!')
    })
  })

  it('displays backend error banner when login rejects', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid username or password.'))
    renderLoginPage()

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    })
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: 'WrongPassword' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Invalid username or password.')).toBeInTheDocument()
  })

  it('redirects to dashboard immediately if already authenticated', () => {
    renderLoginPage({
      isAuthenticated: true,
      user: {
        id: '123',
        username: 'admin',
        is_active: true,
        created_at: '2026-01-01',
      },
    })

    expect(screen.getByText('Dashboard Destination')).toBeInTheDocument()
  })
})


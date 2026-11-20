import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Header from './Header'
import { AuthContext, type AuthContextType } from '../../context/AuthContext'

describe('Header Component', () => {
  const mockLogout = vi.fn()
  const mockMenuClick = vi.fn()

  const defaultAuthValue: AuthContextType = {
    user: {
      id: 'u-1',
      username: 'admin',
      is_active: true,
      created_at: '2026-01-01',
    },
    isAuthenticated: true,
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: mockLogout,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderHeader = (authOverrides = {}) => {
    const authValue = { ...defaultAuthValue, ...authOverrides }
    return render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter>
          <Header onMenuClick={mockMenuClick} />
        </MemoryRouter>
      </AuthContext.Provider>,
    )
  }

  it('renders user avatar with initials and username', () => {
    renderHeader()

    expect(screen.getByTestId('user-avatar')).toHaveTextContent('AD')
    expect(screen.getByTestId('user-display-name')).toHaveTextContent('admin')
    expect(screen.getByTestId('logout-button')).toBeInTheDocument()
  })

  it('calls logout function when the logout button is clicked', async () => {
    mockLogout.mockResolvedValueOnce(undefined)
    renderHeader()

    const logoutButton = screen.getByTestId('logout-button')
    fireEvent.click(logoutButton)

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledOnce()
    })
  })
})


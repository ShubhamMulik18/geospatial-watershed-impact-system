import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getCurrentUser,
  getStoredToken,
  login,
  logout,
  setStoredToken,
} from './authApi'

describe('authApi', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('login sends credentials and stores token on success', async () => {
    const mockResponse = {
      user: {
        id: '123',
        username: 'admin',
        is_active: true,
        created_at: '2026-01-01',
      },
      access_token: 'test_token_abc',
      token_type: 'bearer',
      expires_in: 86400,
    }

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const result = await login('admin', 'AdminPass123!')

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username: 'admin', password: 'AdminPass123!' }),
    })

    expect(result).toEqual(mockResponse)
    expect(getStoredToken()).toBe('test_token_abc')
  })

  it('login throws backend error message on 401', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid username or password.',
          },
        }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )

    await expect(login('admin', 'wrong')).rejects.toThrow('Invalid username or password.')
  })

  it('logout calls endpoint and clears stored token', async () => {
    setStoredToken('existing_token')

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ message: 'Logged out successfully' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const result = await logout()

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/auth/logout', {
      method: 'POST',
      headers: { Authorization: 'Bearer existing_token' },
      credentials: 'include',
    })
    expect(result.message).toBe('Logged out successfully')
    expect(getStoredToken()).toBeNull()
  })

  it('getCurrentUser retrieves current profile with Bearer header', async () => {
    setStoredToken('valid_token')

    const mockUser = {
      id: '123',
      username: 'admin',
      is_active: true,
      created_at: '2026-01-01',
    }

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockUser), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const user = await getCurrentUser()

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/auth/me', {
      method: 'GET',
      headers: { Authorization: 'Bearer valid_token' },
      credentials: 'include',
    })
    expect(user).toEqual(mockUser)
  })

  it('getCurrentUser removes stored token and throws on 401', async () => {
    setStoredToken('invalid_token')

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'SESSION_EXPIRED',
            message: 'Session has expired. Please log in again.',
          },
        }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )

    await expect(getCurrentUser()).rejects.toThrow('Session has expired. Please log in again.')
    expect(getStoredToken()).toBeNull()
  })
})


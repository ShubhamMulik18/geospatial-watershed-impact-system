import type { LoginResponse, LogoutResponse, User } from '../types/auth'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

type BackendErrorResponse = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem('watershed_token')
  } catch {
    return null
  }
}

export const getAuthToken = getStoredToken

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem('watershed_token', token)
    } else {
      localStorage.removeItem('watershed_token')
    }
  } catch {
    // Ignore storage errors
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken()
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as BackendErrorResponse
    if (data.error?.message) {
      return data.error.message
    }
    if (typeof data.detail === 'string') {
      return data.detail
    }
  } catch {
    // Non-JSON response
  }
  return `Authentication request failed with status ${response.status}.`
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  const data = (await response.json()) as LoginResponse
  if (data.access_token) {
    setStoredToken(data.access_token)
  }
  return data
}

export async function logout(): Promise<LogoutResponse> {
  try {
    const headers = getAuthHeaders()
    const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      headers,
      credentials: 'include',
    })
    setStoredToken(null)
    if (!response.ok) {
      return { message: 'Logged out locally' }
    }
    return (await response.json()) as LogoutResponse
  } catch {
    setStoredToken(null)
    return { message: 'Logged out locally' }
  }
}

export async function getCurrentUser(): Promise<User> {
  const headers = getAuthHeaders()
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'GET',
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    setStoredToken(null)
    const message = await getErrorMessage(response)
    throw new Error(message)
  }

  return (await response.json()) as User
}


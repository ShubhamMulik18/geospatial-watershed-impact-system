import React, { createContext, useEffect, useState } from 'react'
import type { User } from '../types/auth'
import { getCurrentUser, login as apiLogin, logout as apiLogout } from '../services/authApi'

export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function checkAuth() {
      try {
        const currentUser = await getCurrentUser()
        if (isMounted) {
          setUser(currentUser)
          setError(null)
        }
      } catch {
        if (isMounted) {
          setUser(null)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    checkAuth()

    return () => {
      isMounted = false
    }
  }, [])

  const login = async (username: string, password: string) => {
    setError(null)
    const result = await apiLogin(username, password)
    setUser(result.user)
  }

  const logout = async () => {
    try {
      await apiLogout()
    } finally {
      setUser(null)
      setError(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        isLoading,
        error,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}


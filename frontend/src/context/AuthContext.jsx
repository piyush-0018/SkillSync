import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getCurrentUser, loginUser, logoutUser, registerUser, updateUserProfile } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const clearSession = useCallback(() => setUser(null), [])

  useEffect(() => {
    let active = true
    getCurrentUser().then((currentUser) => { if (active) setUser(currentUser) })
      .catch(() => { if (active) clearSession() })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [clearSession])

  useEffect(() => {
    window.addEventListener('skillsync:unauthorized', clearSession)
    return () => window.removeEventListener('skillsync:unauthorized', clearSession)
  }, [clearSession])

  const value = useMemo(() => ({
    user,
    isLoading,
    async register(payload) {
      const response = await registerUser(payload)
      setUser(response.user)
      return response.user
    },
    async login(payload) {
      const response = await loginUser(payload)
      setUser(response.user)
      return response.user
    },
    async logout() {
      await logoutUser()
      setUser(null)
    },
    async updateProfile(payload) {
      const updatedUser = await updateUserProfile(payload)
      setUser(updatedUser)
      return updatedUser
    },
  }), [isLoading, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

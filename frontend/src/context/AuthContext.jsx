import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const API = import.meta.env.VITE_API_URL

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async (jwt) => {
    try {
      const res = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${jwt}` },
      })
      if (!res.ok) throw new Error('Invalid token')
      const data = await res.json()
      setUser(data)
      return data
    } catch {
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)
      return null
    }
  }, [])

  useEffect(() => {
    if (token) {
      fetchMe(token).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token, fetchMe])

  const login = async (email, password) => {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Login failed')
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    await fetchMe(data.access_token)
    return data
  }

  const register = async ({ name, email, password, role, department, clearance_level }) => {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role, department, clearance_level }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Registration failed')
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    await fetchMe(data.access_token)
    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const isAuthenticated = !!user && !!token
  const isAdmin = user?.role === 'admin'

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated, isAdmin, login, register, logout, loading }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export default AuthContext

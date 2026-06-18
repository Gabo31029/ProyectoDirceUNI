import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      const stored = localStorage.getItem('sga_auth')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const login = useCallback((data) => {
    // data: { access_token, rol, tenant_id, expires_in, nombre, apellido, id }
    const payload = {
      token: data.access_token,
      rol: data.rol,
      tenantId: data.tenant_id,
      id: data.id || null,
      nombre: data.nombre || '',
      apellido: data.apellido || '',
      expiresAt: Date.now() + data.expires_in * 1000,
    }
    localStorage.setItem('sga_auth', JSON.stringify(payload))
    setAuth(payload)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('sga_auth')
    setAuth(null)
  }, [])

  const isAuthenticated = Boolean(
    auth?.token && auth?.expiresAt && Date.now() < auth.expiresAt
  )

  return (
    <AuthContext.Provider value={{ auth, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

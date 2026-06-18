import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config) => {
    try {
      const stored = localStorage.getItem('sga_auth')
      if (stored) {
        const { token } = JSON.parse(stored)
        if (token) config.headers.Authorization = `Bearer ${token}`
      }
    } catch {
      // ignore parse errors
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sga_auth')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

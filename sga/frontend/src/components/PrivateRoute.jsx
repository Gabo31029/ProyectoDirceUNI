import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function PrivateRoute({ children, roles }) {
  const { isAuthenticated, auth } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (roles && !roles.includes(auth?.rol)) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}

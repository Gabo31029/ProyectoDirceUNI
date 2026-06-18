import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import PrivateRoute from './components/PrivateRoute'

// Pages
import LoginPage from './pages/LoginPage'

// Admin Central
import DashboardAdminCentral from './pages/admin_central/DashboardAdminCentral'
import TenantsPage from './pages/admin_central/TenantsPage'
import CatalogosPage from './pages/admin_central/CatalogosPage'

// Admin
import DashboardAdmin from './pages/admin/DashboardAdmin'
import PeriodosPage from './pages/admin/PeriodosPage'
import OfertaPage from './pages/admin/OfertaPage'
import UsuariosPage from './pages/admin/UsuariosPage'
import CierrePage from './pages/admin/CierrePage'

// Docente
import DashboardDocente from './pages/docente/DashboardDocente'
import CalificacionesPage from './pages/docente/CalificacionesPage'

// Alumno
import DashboardAlumno from './pages/alumno/DashboardAlumno'
import MatriculaPage from './pages/alumno/MatriculaPage'
import HistorialPage from './pages/alumno/HistorialPage'

// Página 404 / Unauthorized
function NotFound() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 16,
      background: 'var(--bg-base)', color: 'var(--text-primary)',
    }}>
      <div style={{ fontSize: '4rem' }}>🔍</div>
      <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Página no encontrada</h1>
      <p style={{ color: 'var(--text-muted)' }}>La ruta solicitada no existe en el sistema.</p>
      <a href="/login" className="btn btn-primary">Ir al inicio de sesión</a>
    </div>
  )
}

function Unauthorized() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 16,
      background: 'var(--bg-base)', color: 'var(--text-primary)',
    }}>
      <div style={{ fontSize: '4rem' }}>🚫</div>
      <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Sin autorización</h1>
      <p style={{ color: 'var(--text-muted)' }}>No tienes permisos para acceder a esta sección.</p>
      <a href="/login" className="btn btn-secondary">Volver al inicio</a>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* ADMIN_CENTRAL */}
          <Route
            path="/admin-central"
            element={
              <PrivateRoute roles={['ADMIN_CENTRAL']}>
                <DashboardAdminCentral />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin-central/tenants"
            element={
              <PrivateRoute roles={['ADMIN_CENTRAL']}>
                <TenantsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin-central/catalogos"
            element={
              <PrivateRoute roles={['ADMIN_CENTRAL']}>
                <CatalogosPage />
              </PrivateRoute>
            }
          />

          {/* ADMIN */}
          <Route
            path="/admin"
            element={
              <PrivateRoute roles={['ADMIN']}>
                <DashboardAdmin />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/periodos"
            element={
              <PrivateRoute roles={['ADMIN']}>
                <PeriodosPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/oferta"
            element={
              <PrivateRoute roles={['ADMIN']}>
                <OfertaPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/usuarios"
            element={
              <PrivateRoute roles={['ADMIN']}>
                <UsuariosPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/cierre"
            element={
              <PrivateRoute roles={['ADMIN']}>
                <CierrePage />
              </PrivateRoute>
            }
          />

          {/* DOCENTE */}
          <Route
            path="/docente"
            element={
              <PrivateRoute roles={['DOCENTE']}>
                <DashboardDocente />
              </PrivateRoute>
            }
          />
          <Route
            path="/docente/calificaciones"
            element={
              <PrivateRoute roles={['DOCENTE']}>
                <CalificacionesPage />
              </PrivateRoute>
            }
          />

          {/* ALUMNO */}
          <Route
            path="/alumno"
            element={
              <PrivateRoute roles={['ALUMNO']}>
                <DashboardAlumno />
              </PrivateRoute>
            }
          />
          <Route
            path="/alumno/matricula"
            element={
              <PrivateRoute roles={['ALUMNO']}>
                <MatriculaPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/alumno/historial"
            element={
              <PrivateRoute roles={['ALUMNO']}>
                <HistorialPage />
              </PrivateRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

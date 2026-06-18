import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import { tenantService } from '../../services/tenantService'

export default function DashboardAdminCentral() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    tenantService.listar()
      .then(setTenants)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const activos = tenants.filter(t => t.estado === 'ACTIVO').length
  const inactivos = tenants.filter(t => t.estado === 'INACTIVO').length

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Panel de Control Central</h1>
            <p className="page-subtitle">Administración global del sistema — ADMIN_CENTRAL</p>
          </div>
        </div>

        <div className="grid-4 mb-6">
          <StatCard icon="🏛️" label="Total Instituciones" value={loading ? '...' : tenants.length} colorClass="indigo" />
          <StatCard icon="✅" label="Activas" value={loading ? '...' : activos} colorClass="green" />
          <StatCard icon="⏸️" label="Inactivas" value={loading ? '...' : inactivos} colorClass="amber" />
          <StatCard icon="🌐" label="Sistema" value="Online" colorClass="blue" />
        </div>

        <div className="grid-2">
          <div className="card">
            <h3 style={{ marginBottom: 12 }}>🏛️ Instituciones Recientes</h3>
            {loading ? (
              <p className="text-muted text-sm">Cargando...</p>
            ) : tenants.length === 0 ? (
              <p className="text-muted text-sm">No hay instituciones registradas aún.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {tenants.slice(0, 5).map(t => (
                  <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{t.nombre}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t.dominio}</div>
                    </div>
                    <span className={`badge ${t.estado === 'ACTIVO' ? 'badge-success' : 'badge-danger'}`}>
                      {t.estado}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 12 }}>⚡ Accesos Rápidos</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { icon: '🏛️', label: 'Gestionar Instituciones', to: '/admin-central/tenants' },
                { icon: '📚', label: 'Configurar Catálogos', to: '/admin-central/catalogos' },
              ].map(item => (
                <a
                  key={item.to}
                  href={item.to}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', textDecoration: 'none',
                    transition: 'all var(--transition)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-500)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                  <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{item.label}</span>
                  <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>→</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { tenantService } from '../../services/tenantService'

export default function DashboardAdminCentral() {
  const navigate = useNavigate()
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
        <div className="page-head">
          <div className="ph-l">
            <h1 className="h1">Panel de Control Central</h1>
            <p className="ph-sub">Administración global del sistema multi-institucional</p>
          </div>
          <div className="page-actions">
            <button className="btn btn-primary" onClick={() => navigate('/admin-central/tenants')}>
              + Nueva institución
            </button>
          </div>
        </div>

        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <StatCard icon="🏛" label="Total Instituciones" value={loading ? '…' : tenants.length} colorClass="indigo" />
          <StatCard icon="✓" label="Activas" value={loading ? '…' : activos} colorClass="green" />
          <StatCard icon="⏸" label="Inactivas" value={loading ? '…' : inactivos} colorClass="amber" />
          <StatCard icon="🌐" label="Sistema" value="Online" colorClass="blue" />
        </div>

        <div className="grid-2">
          {/* Instituciones recientes */}
          <div className="card card-flush">
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--line)' }}>
              <span className="h3">🏛 Instituciones</span>
            </div>
            {loading ? (
              <div style={{ padding: '40px 18px', textAlign: 'center', color: 'var(--ink-3)' }}>Cargando…</div>
            ) : tenants.length === 0 ? (
              <div className="empty">
                <div className="empty-ic">🏛</div>
                <div className="empty-title">Sin instituciones registradas</div>
              </div>
            ) : (
              <div style={{ padding: '0 0 8px' }}>
                {tenants.slice(0, 6).map(t => (
                  <div
                    key={t.id}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '12px 18px', borderBottom: '1px solid var(--line)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--ink)' }}>{t.nombre}</div>
                      <div className="caption">{t.dominio}</div>
                    </div>
                    <Badge value={t.estado} dot />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Accesos rápidos */}
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: '🏛', label: 'Gestionar Instituciones', sub: 'Crear y administrar tenants', to: '/admin-central/tenants' },
                { icon: '📚', label: 'Configurar Catálogos', sub: 'Catálogos globales del sistema', to: '/admin-central/catalogos' },
              ].map(item => (
                <button
                  key={item.to}
                  onClick={() => navigate(item.to)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '11px 14px', borderRadius: 'var(--r-sm)',
                    background: 'var(--surface-2)', border: '1px solid var(--line)',
                    color: 'var(--ink)', cursor: 'pointer', width: '100%', textAlign: 'left',
                    transition: 'border-color .14s, background .14s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--accent-soft)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = 'var(--surface-2)'; }}
                >
                  <span style={{ fontSize: '1.3rem' }}>{item.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.label}</div>
                    <div className="caption">{item.sub}</div>
                  </div>
                  <span style={{ color: 'var(--ink-3)' }}>›</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

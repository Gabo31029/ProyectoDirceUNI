import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import Icon from '../../components/Icon'
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
          <StatCard icon={<Icon name="building" size={18} />} label="Total Instituciones" value={loading ? '…' : tenants.length} colorClass="indigo" />
          <StatCard icon={<Icon name="check-circle" size={18} />} label="Activas" value={loading ? '…' : activos} colorClass="green" />
          <StatCard icon={<Icon name="pause" size={18} />} label="Inactivas" value={loading ? '…' : inactivos} colorClass="amber" />
          <StatCard icon={<Icon name="globe" size={18} />} label="Sistema" value="Online" colorClass="blue" />
        </div>

        <div className="grid-2">
          <div className="card card-flush">
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Icon name="building" size={15} style={{ color: 'var(--ink-3)' }} />
              <span className="h3">Instituciones</span>
            </div>
            {loading ? (
              <div style={{ padding: '40px 18px', textAlign: 'center', color: 'var(--ink-3)' }}>Cargando…</div>
            ) : tenants.length === 0 ? (
              <div className="empty">
                <div className="empty-ic"><Icon name="building" size={32} style={{ color: 'var(--ink-4)' }} /></div>
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

          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: 'building', label: 'Gestionar Instituciones', sub: 'Crear y administrar tenants', to: '/admin-central/tenants' },
                { icon: 'library', label: 'Catálogos globales', sub: 'Escalas, evaluaciones y condiciones', to: '/admin-central/catalogos' },
              ].map(item => (
                <button
                  key={item.to}
                  onClick={() => navigate(item.to)}
                  className="quicklink"
                >
                  <Icon name={item.icon} size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.label}</div>
                    <div className="caption">{item.sub}</div>
                  </div>
                  <Icon name="chevron-right" size={14} style={{ color: 'var(--ink-4)' }} />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

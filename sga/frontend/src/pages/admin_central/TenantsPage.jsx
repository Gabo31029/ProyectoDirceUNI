import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import Badge from '../../components/Badge'
import { tenantService } from '../../services/tenantService'
import { userService } from '../../services/userService'

export default function TenantsPage() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editTenant, setEditTenant] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ nombre: '', dominio: '', zona_horaria: 'America/Lima' })

  // Initial Administrator account states
  const [adminEmail, setAdminEmail] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminNombre, setAdminNombre] = useState('')
  const [adminApellido, setAdminApellido] = useState('')

  const fetchTenants = async () => {
    try {
      setLoading(true)
      setTenants(await tenantService.listar())
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar las instituciones')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchTenants() }, [])

  const openCreate = () => {
    setEditTenant(null)
    setForm({ nombre: '', dominio: '', zona_horaria: 'America/Lima' })
    setAdminEmail('')
    setAdminPassword('')
    setAdminNombre('')
    setAdminApellido('')
    setShowModal(true)
  }

  const openEdit = (t) => {
    setEditTenant(t)
    setForm({ nombre: t.nombre, dominio: t.dominio, zona_horaria: t.zona_horaria })
    setAdminEmail('')
    setAdminPassword('')
    setAdminNombre('')
    setAdminApellido('')
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    const trimmedNombre = form.nombre.trim()
    const trimmedDominio = form.dominio ? form.dominio.trim().toLowerCase() : ''
    const trimmedAdminEmail = adminEmail.trim()
    const trimmedAdminPassword = adminPassword.trim()
    const trimmedAdminNombre = adminNombre.trim()
    const trimmedAdminApellido = adminApellido.trim()

    try {
      if (editTenant) {
        await tenantService.actualizar(editTenant.id, { nombre: trimmedNombre, zona_horaria: form.zona_horaria })
        setSuccess('Institución actualizada correctamente')
      } else {
        // Validation for admin details
        if (!trimmedAdminEmail || !trimmedAdminPassword || !trimmedAdminNombre || !trimmedAdminApellido || !trimmedNombre || !trimmedDominio) {
          setError('Todos los campos son obligatorios.')
          setSaving(false)
          return
        }
        if (trimmedAdminPassword.length < 8) {
          setError('La contraseña del administrador debe tener al menos 8 caracteres.')
          setSaving(false)
          return
        }

        // 1. Create the tenant
        const newTenant = await tenantService.crear({
          nombre: trimmedNombre,
          dominio: trimmedDominio,
          zona_horaria: form.zona_horaria
        })

        // 2. Create the tenant's admin user
        try {
          await userService.crear({
            email: trimmedAdminEmail,
            password: trimmedAdminPassword,
            nombre: trimmedAdminNombre,
            apellido: trimmedAdminApellido,
            rol: 'ADMIN'
          }, newTenant.id)
          setSuccess('Institución y administrador creados correctamente')
        } catch (userErr) {
          setError(`Institución creada, pero falló la creación del administrador: ${userErr.response?.data?.detail || userErr.message}`)
          setSaving(false)
          fetchTenants()
          return
        }
      }
      setShowModal(false)
      fetchTenants()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const toggleEstado = async (t) => {
    try {
      await tenantService.actualizar(t.id, { estado: t.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO' })
      setSuccess('Estado actualizado')
      fetchTenants()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const columns = [
    { accessor: 'nombre', header: 'Nombre', primary: true },
    { accessor: 'dominio', header: 'Dominio' },
    { accessor: 'zona_horaria', header: 'Zona Horaria' },
    { key: 'estado', header: 'Estado', render: row => <Badge value={row.estado} dot /> },
  ]

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Instituciones</h1>
            <p className="page-subtitle">Gestión de tenants del sistema</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <DataTable
          title="Instituciones registradas"
          columns={columns}
          data={tenants}
          loading={loading}
          onAdd={openCreate}
          addLabel="Nueva Institución"
          actions={row => (
            <>
              <button
                id={`btn-edit-tenant-${row.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => openEdit(row)}
              >
                Editar
              </button>
              <button
                id={`btn-toggle-tenant-${row.id}`}
                className={`btn btn-sm ${row.estado === 'ACTIVO' ? 'btn-danger' : 'btn-primary'}`}
                onClick={() => toggleEstado(row)}
              >
                {row.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}
              </button>
            </>
          )}
        />

        {showModal && (
          <Modal
            title={editTenant ? 'Editar Institución' : 'Nueva Institución'}
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-tenant" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Guardando...' : editTenant ? 'Actualizar' : 'Crear'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="form-group">
              <label className="form-label" htmlFor="tenant-nombre">Nombre de la institución</label>
              <input
                id="tenant-nombre"
                className="form-input"
                value={form.nombre}
                onChange={e => setForm({ ...form, nombre: e.target.value })}
                placeholder="Universidad Nacional de..."
                required
                autoComplete="off"
              />
            </div>
            {!editTenant && (
              <div className="form-group">
                <label className="form-label" htmlFor="tenant-dominio">Dominio (slug único)</label>
                <input
                  id="tenant-dominio"
                  className="form-input"
                  value={form.dominio}
                  onChange={e => setForm({ ...form, dominio: e.target.value })}
                  placeholder="ej: uni-lima (solo letras, números y guiones)"
                  required
                />
              </div>
            )}
            <div className="form-group">
              <label className="form-label" htmlFor="tenant-tz">Zona horaria</label>
              <select
                id="tenant-tz"
                className="form-select"
                value={form.zona_horaria}
                onChange={e => setForm({ ...form, zona_horaria: e.target.value })}
              >
                <option value="America/Lima">America/Lima (UTC-5)</option>
                <option value="America/Bogota">America/Bogota (UTC-5)</option>
                <option value="America/Santiago">America/Santiago</option>
                <option value="America/Mexico_City">America/Mexico_City</option>
                <option value="America/Buenos_Aires">America/Buenos_Aires</option>
              </select>
            </div>

            {!editTenant && (
              <>
                <h4 style={{ marginTop: 24, marginBottom: 12, borderTop: '1px solid var(--border-color)', paddingTop: 16 }}>
                  Cuenta del Administrador de la Institución
                </h4>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" htmlFor="admin-nombre">Nombre</label>
                    <input
                      id="admin-nombre"
                      className="form-input"
                      value={adminNombre}
                      onChange={e => setAdminNombre(e.target.value)}
                      placeholder="Nombre del admin"
                      required
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" htmlFor="admin-apellido">Apellido</label>
                    <input
                      id="admin-apellido"
                      className="form-input"
                      value={adminApellido}
                      onChange={e => setAdminApellido(e.target.value)}
                      placeholder="Apellido del admin"
                      required
                    />
                  </div>
                </div>
                <div className="form-group" style={{ marginTop: 12 }}>
                  <label className="form-label" htmlFor="admin-email">Correo Electrónico</label>
                  <input
                    id="admin-email"
                    type="email"
                    className="form-input"
                    value={adminEmail}
                    onChange={e => setAdminEmail(e.target.value)}
                    placeholder="admin@institucion.edu.pe"
                    required
                    autoComplete="off"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="admin-password">Contraseña (mín. 8 caracteres)</label>
                  <input
                    id="admin-password"
                    type="password"
                    className="form-input"
                    value={adminPassword}
                    onChange={e => setAdminPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    autoComplete="new-password"
                  />
                </div>
              </>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  )
}

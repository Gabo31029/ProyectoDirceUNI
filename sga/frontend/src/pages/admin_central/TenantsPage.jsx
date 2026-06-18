import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import Badge from '../../components/Badge'
import { tenantService } from '../../services/tenantService'

export default function TenantsPage() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editTenant, setEditTenant] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ nombre: '', dominio: '', zona_horaria: 'America/Lima' })

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
    setShowModal(true)
  }

  const openEdit = (t) => {
    setEditTenant(t)
    setForm({ nombre: t.nombre, dominio: t.dominio, zona_horaria: t.zona_horaria })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (editTenant) {
        await tenantService.actualizar(editTenant.id, { nombre: form.nombre, zona_horaria: form.zona_horaria })
        setSuccess('Institución actualizada correctamente')
      } else {
        await tenantService.crear(form)
        setSuccess('Institución creada correctamente')
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
                ✏️ Editar
              </button>
              <button
                id={`btn-toggle-tenant-${row.id}`}
                className={`btn btn-sm ${row.estado === 'ACTIVO' ? 'btn-danger' : 'btn-primary'}`}
                onClick={() => toggleEstado(row)}
              >
                {row.estado === 'ACTIVO' ? '⏸️ Desactivar' : '▶️ Activar'}
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
          </Modal>
        )}
      </div>
    </Layout>
  )
}

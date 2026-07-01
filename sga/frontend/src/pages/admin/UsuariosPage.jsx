import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { userService } from '../../services/userService'
import { ofertaService } from '../../services/ofertaService'

const ROLES = ['ALUMNO', 'DOCENTE', 'ADMIN']

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState([])
  const [planes, setPlanes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editUser, setEditUser] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    nombre: '',
    apellido: '',
    email: '',
    password: '',
    rol: 'ALUMNO',
    codigo_alumno: '',
    id_plan_estudios: '',
    periodo_ingreso: ''
  })

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setUsuarios(await userService.listar())
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar usuarios')
    } finally {
      setLoading(false)
    }
  }

  const fetchPlanes = async () => {
    try {
      const data = await ofertaService.listarPlanes()
      setPlanes(data)
    } catch (e) {
      console.error('Error al cargar planes de estudio:', e)
    }
  }

  useEffect(() => {
    fetchUsers()
    fetchPlanes()
  }, [])

  const openCreate = () => {
    setEditUser(null)
    setForm({
      nombre: '',
      apellido: '',
      email: '',
      password: '',
      rol: 'ALUMNO',
      codigo_alumno: '',
      id_plan_estudios: '',
      periodo_ingreso: ''
    })
    setShowModal(true)
  }

  const openEdit = (u) => {
    setEditUser(u)
    setForm({
      nombre: u.nombre,
      apellido: u.apellido,
      email: u.email,
      password: '',
      rol: u.rol,
      codigo_alumno: '',
      id_plan_estudios: '',
      periodo_ingreso: ''
    })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    const trimmedNombre = form.nombre.trim()
    const trimmedApellido = form.apellido.trim()
    const trimmedEmail = form.email.trim()
    const trimmedPassword = form.password.trim()
    const trimmedRol = form.rol

    try {
      if (editUser) {
        const payload = { nombre: trimmedNombre, apellido: trimmedApellido }
        if (form.password) payload.password = trimmedPassword
        await userService.actualizar(editUser.id, payload)
        setSuccess('Usuario actualizado')
      } else {
        // Validation for new user details
        if (!trimmedNombre || !trimmedApellido || !trimmedEmail || !trimmedPassword) {
          setError('Todos los campos son obligatorios.')
          setSaving(false)
          return
        }
        if (trimmedPassword.length < 8) {
          setError('La contraseña debe tener al menos 8 caracteres.')
          setSaving(false)
          return
        }
        const payload = {
          nombre: trimmedNombre,
          apellido: trimmedApellido,
          email: trimmedEmail,
          password: trimmedPassword,
          rol: trimmedRol
        }

        if (trimmedRol === 'ALUMNO') {
          if (!form.codigo_alumno.trim() || !form.id_plan_estudios || !form.periodo_ingreso.trim()) {
            setError('Los campos de perfil del alumno son obligatorios (Código, Plan de Estudios y Periodo de Ingreso).')
            setSaving(false)
            return
          }
          payload.codigo_alumno = form.codigo_alumno.trim()
          payload.id_plan_estudios = form.id_plan_estudios
          payload.periodo_ingreso = form.periodo_ingreso.trim()
        }

        await userService.crear(payload)
        setSuccess('Usuario creado correctamente')
      }
      setShowModal(false)
      fetchUsers()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const handleDesactivar = async (u) => {
    if (!window.confirm(`¿Desactivar a ${u.nombre} ${u.apellido}?`)) return
    try {
      await userService.desactivar(u.id, true)
      setSuccess('Usuario desactivado')
      fetchUsers()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const columns = [
    { key: 'nombre', header: 'Nombre completo', primary: true, render: r => `${r.nombre} ${r.apellido}` },
    { accessor: 'email', header: 'Correo' },
    { key: 'rol', header: 'Rol', render: r => <Badge value={r.rol} /> },
    {
      key: 'activo', header: 'Estado', render: r => (
        <span className={`badge ${r.activo ? 'badge-success' : 'badge-danger'}`}>
          {r.activo ? '● Activo' : '● Inactivo'}
        </span>
      )
    },
  ]

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Gestión de Usuarios</h1>
            <p className="page-subtitle">Administración de docentes, alumnos y administradores</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <DataTable
          title="Usuarios registrados"
          columns={columns}
          data={usuarios}
          loading={loading}
          onAdd={openCreate}
          addLabel="Nuevo Usuario"
          actions={row => (
            <>
              <button
                id={`btn-edit-user-${row.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => openEdit(row)}
              >
                Editar
              </button>
              {row.activo && (
                <button
                  id={`btn-deactivate-user-${row.id}`}
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDesactivar(row)}
                >
                  Desactivar
                </button>
              )}
            </>
          )}
        />

        {showModal && (
          <Modal
            title={editUser ? `Editar — ${editUser.nombre} ${editUser.apellido}` : 'Nuevo Usuario'}
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-user" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Guardando...' : editUser ? 'Actualizar' : 'Crear'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="user-nombre">Nombre</label>
                <input id="user-nombre" className="form-input" value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="user-apellido">Apellido</label>
                <input id="user-apellido" className="form-input" value={form.apellido} onChange={e => setForm({ ...form, apellido: e.target.value })} required />
              </div>
            </div>
            {!editUser && (
              <>
                <div className="form-group">
                  <label className="form-label" htmlFor="user-email">Correo electrónico</label>
                  <input id="user-email" type="email" className="form-input" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="usuario@institucion.edu.pe" required autoComplete="off" />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="user-rol">Rol</label>
                  <select id="user-rol" className="form-select" value={form.rol} onChange={e => setForm({ ...form, rol: e.target.value })}>
                    {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                {form.rol === 'ALUMNO' && (
                  <div className="card" style={{ padding: '1rem', marginTop: '1rem', marginBottom: '1rem', backgroundColor: 'var(--bg-card-secondary, #f8f9fa)', border: '1px solid var(--border-color, #dee2e6)', borderRadius: '6px' }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '1rem', color: 'var(--text-primary)' }}>Detalles de Alumno</h3>
                    <div className="grid-2">
                      <div className="form-group">
                        <label className="form-label" htmlFor="student-code">Código de Alumno</label>
                        <input
                          id="student-code"
                          className="form-input"
                          value={form.codigo_alumno}
                          onChange={e => setForm({ ...form, codigo_alumno: e.target.value })}
                          placeholder="Ej: 20260001"
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label" htmlFor="student-period">Periodo de Ingreso</label>
                        <input
                          id="student-period"
                          className="form-input"
                          value={form.periodo_ingreso}
                          onChange={e => setForm({ ...form, periodo_ingreso: e.target.value })}
                          placeholder="Ej: 2026-1"
                          required
                        />
                      </div>
                    </div>
                    <div className="form-group" style={{ marginTop: '0.5rem' }}>
                      <label className="form-label" htmlFor="student-plan">Plan de Estudios</label>
                      <select
                        id="student-plan"
                        className="form-select"
                        value={form.id_plan_estudios}
                        onChange={e => setForm({ ...form, id_plan_estudios: e.target.value })}
                        required
                      >
                        <option value="">-- Seleccionar Plan de Estudios --</option>
                        {planes.map(p => (
                          <option key={p.id} value={p.id}>
                            {p.carrera} - {p.version_plan} {p.estado === 'ACTIVO' ? '' : '(Borrador)'}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
              </>
            )}
            <div className="form-group">
              <label className="form-label" htmlFor="user-password">
                {editUser ? 'Nueva contraseña (dejar vacío para no cambiar)' : 'Contraseña'}
              </label>
              <input id="user-password" type="password" className="form-input" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Mínimo 8 caracteres" required={!editUser} autoComplete="new-password" />
            </div>
          </Modal>
        )}
      </div>
    </Layout>
  )
}

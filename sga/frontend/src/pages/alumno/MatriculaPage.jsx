import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import Badge from '../../components/Badge'
import Modal from '../../components/Modal'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { periodoService } from '../../services/periodoService'
import { matriculaService } from '../../services/matriculaService'
import { ofertaService } from '../../services/ofertaService'
import { useAuth } from '../../context/AuthContext'

export default function MatriculaPage() {
  const { auth } = useAuth()
  const [periodo, setPeriodo] = useState(null)
  const [matriculas, setMatriculas] = useState([])
  const [inscripciones, setInscripciones] = useState([])
  const [secciones, setSecciones] = useState([])
  const [selectedMatricula, setSelectedMatricula] = useState(null)
  const [showInscModal, setShowInscModal] = useState(false)
  const [showRetiroModal, setShowRetiroModal] = useState(false)
  const [selectedSeccion, setSelectedSeccion] = useState('')
  const [selectedInscripcion, setSelectedInscripcion] = useState(null)
  const [motivo, setMotivo] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const p = await periodoService.activo().catch(() => null)
      setPeriodo(p)
      if (auth?.id) {
        const ms = await matriculaService.listar(auth.id).catch(() => [])
        setMatriculas(ms)
        const activa = ms.find(m => m.estado === 'ACTIVA')
        if (activa) {
          setSelectedMatricula(activa)
          const insc = await matriculaService.listarInscripciones(activa.id).catch(() => [])
          setInscripciones(insc)
        }
        if (p) {
          const secs = await ofertaService.listarSecciones(p.id).catch(() => [])
          setSecciones(secs)
        }
      }
    } finally {
      setLoading(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData() }, [auth?.id])

  useEffect(() => {
    if (!periodo?.id) return
    const interval = setInterval(() => {
      ofertaService.listarSecciones(periodo.id)
        .then(setSecciones)
        .catch(() => {})
    }, 5000) // Poll every 5 seconds to update vacancies in "real-time" for simulations
    return () => clearInterval(interval)
  }, [periodo?.id])

  const handleCrearMatricula = async () => {
    if (!periodo) return
    setSaving(true)
    setError('')
    try {
      await matriculaService.crear({ id_periodo: periodo.id })
      setSuccess('Matrícula creada exitosamente')
      await fetchData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al crear matrícula')
    } finally {
      setSaving(false)
    }
  }

  const handleInscribir = async () => {
    if (!selectedMatricula || !selectedSeccion) return
    setSaving(true)
    setError('')
    try {
      await matriculaService.inscribir(selectedMatricula.id, selectedSeccion)
      setSuccess('Inscripción realizada exitosamente')
      setShowInscModal(false)
      const insc = await matriculaService.listarInscripciones(selectedMatricula.id)
      setInscripciones(insc)
      // Immediately refresh sections/vacancies list
      if (periodo?.id) {
        ofertaService.listarSecciones(periodo.id).then(setSecciones).catch(() => {})
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al inscribirse')
    } finally {
      setSaving(false)
    }
  }

  const handleRetiro = async () => {
    if (!selectedInscripcion) return
    setSaving(true)
    setError('')
    try {
      await matriculaService.retirar(selectedInscripcion.id, motivo)
      setSuccess('Retiro procesado correctamente')
      setShowRetiroModal(false)
      const insc = await matriculaService.listarInscripciones(selectedMatricula.id)
      setInscripciones(insc)
      // Immediately refresh sections/vacancies list
      if (periodo?.id) {
        ofertaService.listarSecciones(periodo.id).then(setSecciones).catch(() => {})
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al procesar el retiro')
    } finally {
      setSaving(false)
    }
  }

  const matriculaActiva = matriculas.find(m => m.estado === 'ACTIVA')
  const seccionesDisponibles = secciones.filter(s => s.estado === 'ABIERTA')

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Mi Matrícula</h1>
            <p className="page-subtitle">Inscripción a secciones y gestión de matrícula</p>
          </div>
          {!matriculaActiva && periodo?.estado === 'MATRICULA' && (
            <button
              id="btn-crear-matricula"
              className="btn btn-primary"
              onClick={handleCrearMatricula}
              disabled={saving}
            >
              {saving ? 'Creando...' : '+ Crear Matrícula'}
            </button>
          )}
          {matriculaActiva && periodo?.estado === 'MATRICULA' && (
            <button
              id="btn-inscribir-seccion"
              className="btn btn-primary"
              onClick={() => { setSelectedSeccion(''); setShowInscModal(true) }}
              disabled={matriculaActiva.fecha_hora_turno && new Date() < new Date(matriculaActiva.fecha_hora_turno)}
            >
              + Inscribir Sección
            </button>
          )}
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        {/* Estado del período */}
        {periodo && (
          <div className={`alert ${periodo.estado === 'MATRICULA' ? 'alert-success' : 'alert-info'} mb-6`}>
            <span>
              Período <strong>{periodo.nombre_periodo}</strong> en estado{' '}
              <Badge value={periodo.estado} />.
              {periodo.estado !== 'MATRICULA' && ' La inscripción de nuevas secciones solo es posible en fase de MATRÍCULA.'}
            </span>
          </div>
        )}

        {/* Matrícula info */}
        {loading ? (
          <div className="loading-container"><div className="spinner" /></div>
        ) : !matriculaActiva ? (
          <div className="card">
            <div className="empty-state">
              <span className="empty-state-icon"></span>
              <span className="empty-state-title">Sin matrícula activa</span>
              <span className="empty-state-text">
                {periodo?.estado === 'MATRICULA'
                  ? 'El período está en fase de matrícula. Crea tu matrícula para inscribirte en secciones.'
                  : 'No hay un período en fase de matrícula disponible actualmente.'}
              </span>
            </div>
          </div>
        ) : (
          <>
            {/* Alerta de Turno de Matrícula */}
            {matriculaActiva.fecha_hora_turno && new Date() < new Date(matriculaActiva.fecha_hora_turno) && (
              <div className="banner banner-danger mb-6" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18 }}>⚠️</span>
                <span>
                  <strong>Aún no es tu turno de matrícula.</strong> Tu ingreso asignado es el <strong>Turno {matriculaActiva.numero_turno}</strong>, programado para iniciar el <strong>{new Date(matriculaActiva.fecha_hora_turno).toLocaleString('es-PE')}</strong>.
                </span>
              </div>
            )}

            {/* Info de matrícula */}
            <div className="card mb-6">
              <h3 style={{ marginBottom: 16 }}>Información de Matrícula</h3>
              <div className="info-grid">
                <div className="info-item">
                  <div className="info-label">Estado</div>
                  <div className="info-value"><Badge value={matriculaActiva.estado} dot /></div>
                </div>
                <div className="info-item">
                  <div className="info-label">Créditos</div>
                  <div className="info-value">{matriculaActiva.creditos_matriculados}</div>
                </div>
                <div className="info-item">
                  <div className="info-label">Fecha de Matrícula</div>
                  <div className="info-value">{new Date(matriculaActiva.fecha_matricula).toLocaleDateString('es-PE')}</div>
                </div>
                {matriculaActiva.numero_turno && (
                  <div className="info-item">
                    <div className="info-label">Turno de Matrícula</div>
                    <div className="info-value">
                      Turno {matriculaActiva.numero_turno} 
                      {matriculaActiva.fecha_hora_turno && ` (Inicia: ${new Date(matriculaActiva.fecha_hora_turno).toLocaleString('es-PE')})`}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Inscripciones */}
            <div className="table-container">
              <div className="table-header">
                <span className="table-title">Mis Inscripciones ({inscripciones.length})</span>
              </div>
              {inscripciones.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon"></span>
                  <span className="empty-state-title">Sin inscripciones</span>
                  <span className="empty-state-text">Inscríbete en secciones disponibles</span>
                </div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Curso</th>
                      <th>Sección</th>
                      <th>Estado</th>
                      <th>Créditos</th>
                      <th>Fecha Inscripción</th>
                      <th>Fecha Retiro</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inscripciones.map(insc => (
                      <tr key={insc.id}>
                        <td className="cell-primary">{insc.nombre_curso || 'Cargando...'}</td>
                        <td>{insc.codigo_seccion || 'Cargando...'}</td>
                        <td><Badge value={insc.estado} dot /></td>
                        <td>{insc.creditos}</td>
                        <td>{new Date(insc.fecha_inscripcion).toLocaleDateString('es-PE')}</td>
                        <td>{insc.fecha_retiro ? new Date(insc.fecha_retiro).toLocaleDateString('es-PE') : '—'}</td>
                        <td>
                          {insc.estado === 'ACTIVA' && periodo?.estado === 'MATRICULA' && (
                            <button
                              id={`btn-retirar-insc-${insc.id}`}
                              className="btn btn-danger btn-sm"
                              onClick={() => { setSelectedInscripcion(insc); setMotivo(''); setShowRetiroModal(true) }}
                            >
                              Retirar
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* Modal Inscripción */}
        {showInscModal && (
          <Modal
            title="Inscribir Sección"
            onClose={() => setShowInscModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowInscModal(false)}>Cancelar</button>
                <button id="btn-confirm-inscripcion" className="btn btn-primary" onClick={handleInscribir} disabled={!selectedSeccion || saving}>
                  {saving ? 'Inscribiendo...' : 'Confirmar Inscripción'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="form-group">
              <label className="form-label" htmlFor="sel-seccion-insc">Sección disponible</label>
              <select id="sel-seccion-insc" className="form-select" value={selectedSeccion} onChange={e => setSelectedSeccion(e.target.value)}>
                <option value="">— Selecciona una sección —</option>
                {seccionesDisponibles.map(s => (
                  <option key={s.id} value={s.id}>
                    Sección {s.codigo_seccion} — {s.vacantes_disponibles} vacantes disponibles
                  </option>
                ))}
              </select>
            </div>
            {seccionesDisponibles.length === 0 && (
              <p className="text-muted text-sm">No hay secciones disponibles para este período.</p>
            )}
          </Modal>
        )}

        {/* Modal Retiro */}
        {showRetiroModal && (
          <Modal
            title="Retiro de Sección"
            onClose={() => setShowRetiroModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowRetiroModal(false)}>Cancelar</button>
                <button id="btn-confirm-retiro" className="btn btn-danger" onClick={handleRetiro} disabled={saving}>
                  {saving ? 'Procesando...' : 'Confirmar Retiro'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="alert alert-warning mb-4">
              <span>Estás a punto de retirarte de esta sección. Verifica que estás dentro del período de retiro.</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="retiro-motivo">Motivo (opcional)</label>
              <textarea id="retiro-motivo" className="form-textarea" value={motivo} onChange={e => setMotivo(e.target.value)} placeholder="Describe el motivo del retiro..." />
            </div>
          </Modal>
        )}
      </div>
    </Layout>
  )
}

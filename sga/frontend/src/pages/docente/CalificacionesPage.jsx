import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { periodoService } from '../../services/periodoService'
import { ofertaService } from '../../services/ofertaService'
import { calificacionService } from '../../services/calificacionService'
import { matriculaService } from '../../services/matriculaService'

export default function CalificacionesPage() {
  const [periodos, setPeriodos] = useState([])
  const [selectedPeriodo, setSelectedPeriodo] = useState('')
  const [secciones, setSecciones] = useState([])
  const [selectedSeccion, setSelectedSeccion] = useState('')
  const [evaluaciones, setEvaluaciones] = useState([])
  const [selectedEvaluacion, setSelectedEvaluacion] = useState('')
  const [inscripciones, setInscripciones] = useState([])
  const [notas, setNotas] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)
  const [showCorrectModal, setShowCorrectModal] = useState(false)
  const [correccionForm, setCorreccionForm] = useState({ valor_nuevo: '', justificacion: '' })
  const [selectedCalif, setSelectedCalif] = useState(null)

  useEffect(() => {
    periodoService.listar().then(list => {
      setPeriodos(list)
      const activo = list.find(p => p.estado === 'REGISTRO_NOTAS')
      if (activo) setSelectedPeriodo(activo.id)
      else if (list.length > 0) setSelectedPeriodo(list[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedPeriodo) return
    ofertaService.listarSecciones(selectedPeriodo)
      .then(list => { setSecciones(list); setSelectedSeccion(''); setEvaluaciones([]); setSelectedEvaluacion('') })
      .catch(() => setSecciones([]))
  }, [selectedPeriodo])

  useEffect(() => {
    if (!selectedSeccion) return
    ofertaService.listarEvaluaciones(selectedSeccion)
      .then(list => { setEvaluaciones(list); setSelectedEvaluacion('') })
      .catch(() => setEvaluaciones([]))
  }, [selectedSeccion])

  useEffect(() => {
    if (!selectedSeccion) { setInscripciones([]); return }
    setInscripciones([])
  }, [selectedSeccion])

  const evalObj = evaluaciones.find(c => c.id === selectedEvaluacion)

  const handleRegistrar = async () => {
    if (!selectedSeccion || !selectedEvaluacion) return
    const calificaciones = Object.entries(notas)
      .filter(([, v]) => v !== '')
      .map(([id_inscripcion, valor_nota]) => ({ id_inscripcion, valor_nota: parseFloat(valor_nota) }))
    if (calificaciones.length === 0) {
      setError('Agrega al menos una calificación')
      return
    }
    setSaving(true)
    setError('')
    try {
      await calificacionService.registrar(selectedSeccion, selectedEvaluacion, calificaciones)
      setSuccess(`${calificaciones.length} calificación(es) registrada(s) en borrador`)
      setNotas({})
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al registrar')
    } finally {
      setSaving(false)
    }
  }

  const handlePublicar = async (evalId) => {
    if (!window.confirm('¿Publicar esta evaluación? Los alumnos podrán ver sus notas.')) return
    try {
      await calificacionService.publicar(selectedSeccion, evalId)
      setSuccess('Evaluación publicada correctamente')
      ofertaService.listarEvaluaciones(selectedSeccion).then(setEvaluaciones)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al publicar')
    }
  }

  const handleCorreccion = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await calificacionService.corregir(selectedCalif, parseFloat(correccionForm.valor_nuevo), correccionForm.justificacion)
      setSuccess('Corrección aplicada')
      setShowCorrectModal(false)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error en la corrección')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Gestión de Calificaciones</h1>
            <p className="page-subtitle">Registro, publicación y corrección de notas</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        {/* Filtros */}
        <div className="card mb-6">
          <h3 style={{ marginBottom: 16 }}>Seleccionar Sección y Evaluación</h3>
          <div className="grid-3">
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" htmlFor="sel-periodo-cal">Período</label>
              <select id="sel-periodo-cal" className="form-select" value={selectedPeriodo} onChange={e => setSelectedPeriodo(e.target.value)}>
                {periodos.map(p => <option key={p.id} value={p.id}>{p.nombre_periodo}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" htmlFor="sel-seccion-cal">Sección</label>
              <select id="sel-seccion-cal" className="form-select" value={selectedSeccion} onChange={e => setSelectedSeccion(e.target.value)}>
                <option value="">— Selecciona sección —</option>
                {secciones.map(s => <option key={s.id} value={s.id}>Sección {s.codigo_seccion}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" htmlFor="sel-eval-cal">Evaluación Académica</label>
              <select id="sel-eval-cal" className="form-select" value={selectedEvaluacion} onChange={e => setSelectedEvaluacion(e.target.value)}>
                <option value="">— Selecciona evaluación —</option>
                {evaluaciones.map(c => <option key={c.id} value={c.id}>Peso {c.peso_relativo}% — {c.estado}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Evaluaciones de la sección */}
        {selectedSeccion && (
          <div className="card mb-6">
            <h3 style={{ marginBottom: 16 }}>Evaluaciones de la Sección</h3>
            {evaluaciones.length === 0 ? (
              <p className="text-muted text-sm">No hay evaluaciones configuradas en esta sección.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Peso Relativo</th>
                    <th>Orden</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluaciones.map(comp => (
                    <tr key={comp.id}>
                      <td className="cell-primary">{comp.peso_relativo}%</td>
                      <td>{comp.orden_presentacion || '—'}</td>
                      <td><Badge value={comp.estado} dot /></td>
                      <td>
                        <div className="table-actions">
                          {comp.estado === 'BORRADOR' && (
                            <button
                              id={`btn-publicar-eval-${comp.id}`}
                              className="btn btn-primary btn-sm"
                              onClick={() => handlePublicar(comp.id)}
                            >
                              Publicar
                            </button>
                          )}
                          {comp.estado === 'CERRADO' && (
                            <button
                              id={`btn-corregir-eval-${comp.id}`}
                              className="btn btn-secondary btn-sm"
                              onClick={() => { setSelectedCalif(comp.id); setShowCorrectModal(true) }}
                            >
                              Corrección
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Registro de calificaciones */}
        {selectedSeccion && selectedEvaluacion && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3>Registrar Calificaciones</h3>
              {evalObj && <Badge value={evalObj.estado} dot />}
            </div>

            <div className="alert alert-info mb-4">
              <span>Info:</span>
              <span>Ingresa el ID de inscripción y la nota del alumno. Las notas se guardan en estado <strong>BORRADOR</strong> hasta publicar la evaluación.</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[1, 2, 3].map(i => (
                <div key={i} className="grid-2" style={{ gap: 12 }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" htmlFor={`inscr-id-${i}`}>ID Inscripción #{i}</label>
                    <input
                      id={`inscr-id-${i}`}
                      className="form-input"
                      placeholder="UUID de la inscripción"
                      value={Object.keys(notas)[i - 1] || ''}
                      onChange={e => {
                        const newNotas = { ...notas }
                        const keys = Object.keys(newNotas)
                        const oldKey = keys[i - 1]
                        if (oldKey) delete newNotas[oldKey]
                        if (e.target.value) newNotas[e.target.value] = Object.values(notas)[i - 1] || ''
                        setNotas(newNotas)
                      }}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" htmlFor={`nota-val-${i}`}>Nota #{i}</label>
                    <input
                      id={`nota-val-${i}`}
                      type="number"
                      min="0"
                      step="0.1"
                      className="form-input"
                      placeholder="0.0 - 20.0"
                      value={Object.values(notas)[i - 1] || ''}
                      onChange={e => {
                        const newNotas = { ...notas }
                        const key = Object.keys(notas)[i - 1]
                        if (key) newNotas[key] = e.target.value
                        setNotas(newNotas)
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="modal-footer" style={{ paddingBottom: 0 }}>
              <button
                id="btn-registrar-calificaciones"
                className="btn btn-primary"
                onClick={handleRegistrar}
                disabled={saving || evalObj?.estado === 'CERRADO'}
              >
                {saving ? 'Registrando...' : 'Registrar Calificaciones'}
              </button>
            </div>
          </div>
        )}

        {/* Modal corrección */}
        {showCorrectModal && (
          <Modal
            title="Corrección de Calificación"
            onClose={() => setShowCorrectModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowCorrectModal(false)}>Cancelar</button>
                <button id="btn-save-correccion" className="btn btn-primary" onClick={handleCorreccion} disabled={saving}>
                  {saving ? 'Aplicando...' : 'Aplicar Corrección'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="alert alert-warning">
              <span>La corrección de calificaciones es un acto académico formal y queda registrado en auditoría.</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="corr-valor">Nueva Calificación</label>
              <input id="corr-valor" type="number" min="0" step="0.1" className="form-input" value={correccionForm.valor_nuevo} onChange={e => setCorreccionForm({ ...correccionForm, valor_nuevo: e.target.value })} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="corr-justif">Justificación (mín. 5 caracteres)</label>
              <textarea id="corr-justif" className="form-textarea" value={correccionForm.justificacion} onChange={e => setCorreccionForm({ ...correccionForm, justificacion: e.target.value })} placeholder="Describe la razón de la corrección..." required />
            </div>
          </Modal>
        )}
      </div>
    </Layout>
  )
}

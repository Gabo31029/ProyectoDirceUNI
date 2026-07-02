import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { periodoService } from '../../services/periodoService'
import { tenantService } from '../../services/tenantService'
import { useAuth } from '../../context/AuthContext'

const ESTADOS = ['CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO']
const TABS_POLITICAS = ['Turnos de Matrícula', 'Condición', 'Retiro', 'Reserva', 'Dispersión']

const LABEL_MAP = {
  tipo_condicion: 'Condición Académica',
  cuenta_evaluada: 'Evaluación del Alumno de',
  umbral: 'Umbral',
  operador: 'Operador',
  accion_resultante: 'Acción Resultante',
  fecha_hora_inicio: 'Fecha Inicio',
  creditos_maximos: 'Créditos Máx.',
  ppa_minimo: 'PPA Mín.',
  ppa_maximo: 'PPA Máx.',
  tipo_retiro: 'Tipo Retiro',
  semana_limite: 'Semana Límite',
  condiciones_bloqueantes: 'Bloqueante',
  max_periodos_consecutivos: 'Consecutivos Máx.',
  max_periodos_alternos: 'Alternos Máx.',
  tipo_promedio: 'Tipo Promedio',
  expresion_calculo: 'Fórmula',
  exponente_dispersion: 'Exponente Dispersión'
}

export default function PeriodosPage() {
  const [periodos, setPeriodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showPoliticasModal, setShowPoliticasModal] = useState(false)
  const [showTransModal, setShowTransModal] = useState(false)
  const [selectedPeriodo, setSelectedPeriodo] = useState(null)
  const [politicasTab, setPoliticasTab] = useState(0)
  const [politicasData, setPoliticasData] = useState([])
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ nombre_periodo: '', fecha_inicio: '', fecha_fin: '' })
  const [polForm, setPolForm] = useState({})
  const [transEstado, setTransEstado] = useState('')
  const [tiposCondicion, setTiposCondicion] = useState([])
  const { auth } = useAuth()

  const fetchPeriodos = async () => {
    try {
      setLoading(true)
      setPeriodos(await periodoService.listar())
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar períodos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPeriodos() }, [])

  const loadPoliticas = async (periodoId, tab) => {
    try {
      let result = []
      if (tab === 0) result = await periodoService.listarPoliticasTurno(periodoId)
      else if (tab === 1) result = await periodoService.listarPoliticasCondicion(periodoId)
      else if (tab === 2) result = await periodoService.listarPoliticasRetiro(periodoId)
      else if (tab === 3) {
        const r = await periodoService.obtenerPoliticaReserva(periodoId)
        result = r ? [r] : []
      }
      else if (tab === 4) {
        const r = await periodoService.obtenerDispersion(periodoId)
        result = r ? [r] : []
      }
      setPoliticasData(result)
    } catch { setPoliticasData([]) }
  }

  const openPoliticas = async (p) => {
    setSelectedPeriodo(p)
    setPoliticasTab(0)
    await loadPoliticas(p.id, 0)
    try {
      const tc = await tenantService.listarTiposCondicion(auth.tenantId)
      setTiposCondicion(tc)
    } catch (err) {
      console.error(err)
    }
    setShowPoliticasModal(true)
    setPolForm({})
  }

  const handleTabChange = async (tab) => {
    setPoliticasTab(tab)
    if (selectedPeriodo) await loadPoliticas(selectedPeriodo.id, tab)
    setPolForm({})
  }

  const handleCrearPeriodo = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await periodoService.crear(form)
      setSuccess('Período creado exitosamente')
      setShowModal(false)
      fetchPeriodos()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al crear período')
    } finally {
      setSaving(false)
    }
  }

  const handleTransicion = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await periodoService.transicionar(selectedPeriodo.id, transEstado)
      setSuccess(`Período transicionado a ${transEstado}`)
      setShowTransModal(false)
      fetchPeriodos()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error en la transición')
    } finally {
      setSaving(false)
    }
  }

  const handleCrearPolitica = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const id = selectedPeriodo.id
      if (politicasTab === 0) await periodoService.crearPoliticaTurno(id, polForm)
      else if (politicasTab === 1) await periodoService.crearPoliticaCondicion(id, polForm)
      else if (politicasTab === 2) await periodoService.crearPoliticaRetiro(id, polForm)
      else if (politicasTab === 3) await periodoService.crearPoliticaReserva(id, polForm)
      else if (politicasTab === 4) await periodoService.crearDispersion(id, polForm)
      setSuccess('Política agregada')
      setPolForm({})
      await loadPoliticas(id, politicasTab)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar política')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { accessor: 'nombre_periodo', header: 'Nombre Período', primary: true },
    { accessor: 'fecha_inicio', header: 'Inicio' },
    { accessor: 'fecha_fin', header: 'Fin' },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
    { key: 'creado', header: 'Creado', render: r => new Date(r.created_at).toLocaleDateString('es-PE') },
  ]

  const nextEstado = (est) => {
    const idx = ESTADOS.indexOf(est)
    return idx < ESTADOS.length - 1 ? ESTADOS[idx + 1] : null
  }

  const renderPolForm = () => {
    const f = polForm
    const set = (k, v) => setPolForm({ ...f, [k]: v })
    if (politicasTab === 0) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-num-turno">Número de Turno</label>
          <input id="pol-num-turno" type="number" className="form-input" value={f.numero_turno || ''} onChange={e => set('numero_turno', parseInt(e.target.value))} placeholder="ej: 1" required />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-fecha-inicio-turno">Fecha y Hora de Inicio</label>
          <input id="pol-fecha-inicio-turno" type="datetime-local" className="form-input" value={f.fecha_hora_inicio || ''} onChange={e => set('fecha_hora_inicio', e.target.value)} required />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-cred-max">Créditos Máximos del Turno</label>
          <input id="pol-cred-max" type="number" className="form-input" value={f.creditos_maximos || ''} onChange={e => set('creditos_maximos', parseInt(e.target.value))} placeholder="ej: 22" required />
        </div>
      </div>
    )
    if (politicasTab === 1) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-tipo-condicion">Tipo de Condición Académica</label>
          <select 
            id="pol-tipo-condicion" 
            className="form-select" 
            value={f.id_tipo_condicion || ''} 
            onChange={e => set('id_tipo_condicion', e.target.value)}
            required
          >
            <option value="">Selecciona...</option>
            {tiposCondicion.map(tc => (
              <option key={tc.id} value={tc.id}>{tc.nombre} ({tc.codigo})</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-cuenta">Evaluación de condición del alumno de:</label>
          <select id="pol-cuenta" className="form-select" value={f.cuenta_evaluada || ''} onChange={e => set('cuenta_evaluada', e.target.value)}>
            <option value="">Selecciona...</option>
            <option value="CTA-DESAPROBACIONES">Cursos Desaprobados (CTA-DESAPROBACIONES)</option>
            <option value="CTA-CREDITOS-APROBADOS">Créditos Aprobados (CTA-CREDITOS-APROBADOS)</option>
            <option value="CTA-CREDITOS-INSCRITOS">Créditos Inscritos (CTA-CREDITOS-INSCRITOS)</option>
            <option value="CTA-RESERVAS-MATRICULA">Reservas de Matrícula (CTA-RESERVAS-MATRICULA)</option>
            <option value="CTA-CONDICION-ACADEMICA">Condición Académica (CTA-CONDICION-ACADEMICA)</option>
            <option value="CTA-PROMEDIO-SNAPSHOT">Snapshot de Promedio (CTA-PROMEDIO-SNAPSHOT)</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-umbral">Umbral</label>
          <input id="pol-umbral" type="number" step="0.01" className="form-input" value={f.umbral || ''} onChange={e => set('umbral', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-operador">Operador</label>
          <select id="pol-operador" className="form-select" value={f.operador || ''} onChange={e => set('operador', e.target.value)}>
            <option value="">Selecciona...</option>
            {['MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE'].map(o => <option key={o} value={o}>{o.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-accion">Acción Resultante</label>
          <input id="pol-accion" className="form-input" value={f.accion_resultante || ''} onChange={e => set('accion_resultante', e.target.value)} />
        </div>
      </div>
    )
    if (politicasTab === 2) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-tipo-ret">Tipo de Retiro</label>
          <input id="pol-tipo-ret" className="form-input" value={f.tipo_retiro || ''} onChange={e => set('tipo_retiro', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-sem-lim">Semana Límite</label>
          <input id="pol-sem-lim" type="number" className="form-input" value={f.semana_limite || ''} onChange={e => set('semana_limite', parseInt(e.target.value))} />
        </div>
      </div>
    )
    if (politicasTab === 3) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-max-cons">Máx. Períodos Consecutivos</label>
          <input id="pol-max-cons" type="number" className="form-input" value={f.max_periodos_consecutivos || ''} onChange={e => set('max_periodos_consecutivos', parseInt(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-max-alt">Máx. Períodos Alternos</label>
          <input id="pol-max-alt" type="number" className="form-input" value={f.max_periodos_alternos || ''} onChange={e => set('max_periodos_alternos', parseInt(e.target.value))} />
        </div>
      </div>
    )
    if (politicasTab === 4) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-ciclos">Ciclos Máx. Dispersión</label>
          <input id="pol-ciclos" type="number" className="form-input" value={f.ciclos_max_dispersion || ''} onChange={e => set('ciclos_max_dispersion', parseInt(e.target.value))} />
        </div>
        <div className="form-group" style={{ justifyContent: 'center' }}>
          <label className="form-label">Prioridad Ciclo Atrasado</label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input type="checkbox" checked={!!f.prioridad_ciclo_atrasado} onChange={e => set('prioridad_ciclo_atrasado', e.target.checked)} />
            <span className="text-sm">Activar prioridad de ciclo atrasado</span>
          </label>
        </div>
      </div>
    )
    return null
  }

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Períodos Académicos</h1>
            <p className="page-subtitle">Creación, transición de estados y configuración de políticas</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <DataTable
          title="Períodos académicos"
          columns={columns}
          data={periodos}
          loading={loading}
          onAdd={() => { setShowModal(true); setForm({ nombre_periodo: '', fecha_inicio: '', fecha_fin: '' }) }}
          addLabel="Nuevo Período"
          actions={row => (
            <>
              <button
                id={`btn-politicas-${row.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => openPoliticas(row)}
              >
                Políticas
              </button>
              {nextEstado(row.estado) && (
                <button
                  id={`btn-trans-${row.id}`}
                  className="btn btn-primary btn-sm"
                  onClick={() => { setSelectedPeriodo(row); setTransEstado(nextEstado(row.estado)); setShowTransModal(true) }}
                >
                  {nextEstado(row.estado)}
                </button>
              )}
            </>
          )}
        />

        {/* Crear Período */}
        {showModal && (
          <Modal
            title="Nuevo Período Académico"
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-periodo" className="btn btn-primary" onClick={handleCrearPeriodo} disabled={saving}>
                  {saving ? 'Creando...' : 'Crear Período'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="form-group">
              <label className="form-label" htmlFor="periodo-nombre">Nombre del período</label>
              <input id="periodo-nombre" className="form-input" value={form.nombre_periodo} onChange={e => setForm({ ...form, nombre_periodo: e.target.value })} placeholder="ej: 2026-I" required />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="periodo-inicio">Fecha inicio</label>
                <input id="periodo-inicio" type="date" className="form-input" value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="periodo-fin">Fecha fin</label>
                <input id="periodo-fin" type="date" className="form-input" value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} required />
              </div>
            </div>
          </Modal>
        )}

        {/* Transición de estado */}
        {showTransModal && selectedPeriodo && (
          <Modal
            title={`Transicionar Período`}
            onClose={() => setShowTransModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowTransModal(false)}>Cancelar</button>
                <button id="btn-confirm-trans" className="btn btn-primary" onClick={handleTransicion} disabled={saving}>
                  {saving ? 'Procesando...' : `Confirmar → ${transEstado}`}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="alert alert-warning">
              <span>
                Vas a transicionar <strong>{selectedPeriodo.nombre_periodo}</strong> de{' '}
                <strong>{selectedPeriodo.estado}</strong> → <strong>{transEstado}</strong>.<br />
                Esta operación no se puede deshacer fácilmente.
              </span>
            </div>
          </Modal>
        )}

        {/* Políticas del período */}
        {showPoliticasModal && selectedPeriodo && (
          <Modal
            title={`Políticas — ${selectedPeriodo.nombre_periodo}`}
            onClose={() => setShowPoliticasModal(false)}
            size="lg"
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <SuccessAlert message={success} onClose={() => setSuccess('')} />
            <div className="tabs" style={{ marginBottom: 16 }}>
              {TABS_POLITICAS.map((tab, i) => (
                <button
                  key={tab}
                  id={`tab-politica-${i}`}
                  className={`tab-btn${politicasTab === i ? ' active' : ''}`}
                  onClick={() => handleTabChange(i)}
                  style={{ fontSize: '0.78rem', padding: '7px 12px' }}
                >
                  {tab}
                </button>
              ))}
            </div>

            <form onSubmit={handleCrearPolitica}>
              {renderPolForm()}
              <button id="btn-add-politica" type="submit" className="btn btn-primary btn-sm" disabled={saving}>
                {saving ? 'Guardando...' : '+ Agregar política'}
              </button>
            </form>

            {politicasData.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <h4 style={{ marginBottom: 12 }}>Políticas configuradas</h4>
                {politicasData.map((p, i) => (
                  <div key={p.id || i} style={{
                    background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)',
                    padding: '12px 16px', marginBottom: 8, fontSize: '0.825rem',
                    border: '1px solid var(--border)'
                  }}>
                    {Object.entries(p).filter(([k]) => !['id', 'id_periodo', 'id_tenant', 'id_tipo_condicion', 'codigo_condicion', 'created_at'].includes(k)).map(([k, v]) => (
                      <span key={k} style={{ marginRight: 16, color: 'var(--text-secondary)' }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{LABEL_MAP[k] || k}:</strong>{' '}
                        {k === 'fecha_hora_inicio' ? new Date(v).toLocaleString('es-PE') : String(v)}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  )
}

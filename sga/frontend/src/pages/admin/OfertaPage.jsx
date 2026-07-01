import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { ofertaService } from '../../services/ofertaService'
import { periodoService } from '../../services/periodoService'

const TABS = ['Planes de Estudio', 'Cursos', 'Secciones']

export default function OfertaPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [planes, setPlanes] = useState([])
  const [cursos, setCursos] = useState([])
  const [secciones, setSecciones] = useState([])
  const [periodos, setPeriodos] = useState([])
  const [selectedPeriodo, setSelectedPeriodo] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState('')
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  // Estados añadidos para Malla Curricular y Prerrequisitos
  const [selectedPlanForMalla, setSelectedPlanForMalla] = useState(null)
  const [cursosPlan, setCursosPlan] = useState([])
  const [showAsociarModal, setShowAsociarModal] = useState(false)
  const [asociarCiclo, setAsociarCiclo] = useState(1)
  const [asociarForm, setAsociarForm] = useState({ id_curso: '', es_obligatorio: true })
  const [selectedPrereqs, setSelectedPrereqs] = useState([])

  const load = async () => {
    setLoading(true)
    try {
      if (activeTab === 0) {
        setPlanes(await ofertaService.listarPlanes())
        // Recargar el plan seleccionado si ya estamos en la vista de malla
        if (selectedPlanForMalla) {
          const cp = await ofertaService.listarCursosPlan(selectedPlanForMalla.id)
          setCursosPlan(cp)
        }
      }
      else if (activeTab === 1) setCursos(await ofertaService.listarCursos())
      else if (activeTab === 2 && selectedPeriodo) setSecciones(await ofertaService.listarSecciones(selectedPeriodo))
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    periodoService.listar().then(list => {
      setPeriodos(list)
      if (list.length > 0) setSelectedPeriodo(list[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => { load() }, [activeTab, selectedPeriodo])

  const openModal = (type) => {
    setModalType(type)
    setForm({})
    setSelectedPrereqs([])
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (modalType === 'plan') {
        await ofertaService.crearPlan(form)
        setSuccess('Plan de estudios creado')
      } else if (modalType === 'curso') {
        await ofertaService.crearCurso({ ...form, prerrequisitos: selectedPrereqs })
        setSuccess('Curso creado')
      } else if (modalType === 'seccion') {
        await ofertaService.crearSeccion({ ...form, id_periodo: selectedPeriodo })
        setSuccess('Sección creada')
      }
      setShowModal(false)
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const activarPlan = async (planId) => {
    try {
      await ofertaService.activarPlan(planId)
      setSuccess('Plan activado')
      // Actualizar el plan localmente en caso de que esté abierto en la vista de malla
      if (selectedPlanForMalla && selectedPlanForMalla.id === planId) {
        setSelectedPlanForMalla(prev => ({ ...prev, estado: 'ACTIVO' }))
      }
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const handlePrereqChange = (cursoId) => {
    setSelectedPrereqs(prev => 
      prev.includes(cursoId) ? prev.filter(id => id !== cursoId) : [...prev, cursoId]
    )
  }

  const gestionarMalla = async (plan) => {
    setSelectedPlanForMalla(plan)
    try {
      const cp = await ofertaService.listarCursosPlan(plan.id)
      setCursosPlan(cp)
    } catch (e) {
      setError('Error al obtener cursos del plan')
    }
  }

  const desasociarCurso = async (cursoId) => {
    try {
      await ofertaService.desasociarCursoDePlan(selectedPlanForMalla.id, cursoId)
      setSuccess('Curso desasociado del plan')
      const cp = await ofertaService.listarCursosPlan(selectedPlanForMalla.id)
      setCursosPlan(cp)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al quitar el curso')
    }
  }

  const handleAsociarCurso = async (e) => {
    e.preventDefault()
    if (!asociarForm.id_curso) {
      setError('Debe seleccionar un curso')
      return
    }
    try {
      await ofertaService.asociarCursoAPlan(selectedPlanForMalla.id, {
        id_curso: asociarForm.id_curso,
        ciclo_en_plan: asociarCiclo,
        es_obligatorio: asociarForm.es_obligatorio,
      })
      setSuccess('Curso asociado al plan')
      setShowAsociarModal(false)
      const cp = await ofertaService.listarCursosPlan(selectedPlanForMalla.id)
      setCursosPlan(cp)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al asociar el curso')
    }
  }

  const planesColumns = [
    { accessor: 'carrera', header: 'Carrera', primary: true },
    { accessor: 'version_plan', header: 'Versión' },
    { accessor: 'creditos_totales', header: 'Créditos Totales' },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
  ]

  const cursosColumns = [
    { accessor: 'codigo_curso', header: 'Código', primary: true },
    { accessor: 'nombre_curso', header: 'Nombre del Curso' },
    { accessor: 'creditos', header: 'Créditos' },
    { key: 'tipo', header: 'Tipo', render: r => <Badge value={r.tipo_curso} /> },
    { accessor: 'ciclo_sugerido', header: 'Ciclo' },
  ]

  const seccionesColumns = [
    { accessor: 'codigo_seccion', header: 'Código Sección', primary: true },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
    { accessor: 'vacantes_maximas', header: 'Vacantes Máx.' },
    { accessor: 'vacantes_disponibles', header: 'Disponibles' },
  ]

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Oferta Académica</h1>
            <p className="page-subtitle">Planes de estudio, cursos y secciones por período</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
          <div className="tabs" style={{ margin: 0 }}>
            {TABS.map((tab, i) => (
              <button
                key={tab}
                id={`tab-oferta-${i}`}
                className={`tab-btn${activeTab === i ? ' active' : ''}`}
                onClick={() => {
                  setActiveTab(i)
                  setSelectedPlanForMalla(null)
                }}
              >
                {tab}
              </button>
            ))}
          </div>
          {activeTab === 2 && (
            <select
              id="select-periodo-oferta"
              className="form-select"
              style={{ width: 200 }}
              value={selectedPeriodo}
              onChange={e => setSelectedPeriodo(e.target.value)}
            >
              {periodos.map(p => <option key={p.id} value={p.id}>{p.nombre_periodo}</option>)}
            </select>
          )}
        </div>

        {activeTab === 0 && (
          selectedPlanForMalla ? (
            <div className="card animate-fade-in" style={{ padding: 24, marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid var(--border-color, #e2e8f0)', paddingBottom: 16 }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    Malla Curricular: {selectedPlanForMalla.carrera} 
                    <span style={{ fontSize: '1rem', color: 'var(--text-muted, #718096)' }}>({selectedPlanForMalla.version_plan})</span>
                    <Badge value={selectedPlanForMalla.estado} dot />
                  </h2>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted, #718096)', marginTop: 4 }}>
                    ID Plan: {selectedPlanForMalla.id} | Créditos Totales: {selectedPlanForMalla.creditos_totales}
                  </p>
                </div>
                <button 
                  id="btn-volver-planes"
                  className="btn btn-secondary" 
                  onClick={() => setSelectedPlanForMalla(null)}
                >
                  Volver a Planes
                </button>
              </div>

              {/* Grid de 10 Ciclos */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map(ciclo => {
                  const cursosCiclo = cursosPlan.filter(c => c.ciclo_en_plan === ciclo)
                  return (
                    <div 
                      key={ciclo} 
                      className="card" 
                      style={{ 
                        padding: 16, 
                        border: '1px solid var(--border-color, #e2e8f0)', 
                        background: 'var(--bg-card, #f8fafc)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        minHeight: '200px'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, borderBottom: '1px solid var(--border-color, #e2e8f0)', paddingBottom: 8 }}>
                          <h3 style={{ fontWeight: 600, margin: 0 }}>Ciclo {ciclo}</h3>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #718096)' }}>
                            {cursosCiclo.length} {cursosCiclo.length === 1 ? 'curso' : 'cursos'}
                          </span>
                        </div>

                        {cursosCiclo.length === 0 ? (
                          <p style={{ fontStyle: 'italic', fontSize: '0.875rem', color: 'var(--text-muted, #a0aec0)', padding: '16px 0', textAlign: 'center', margin: 0 }}>
                            Sin cursos asignados
                          </p>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
                            {cursosCiclo.map(c => {
                              // Buscar nombres de los prerrequisitos en la lista general de cursos
                              const prereqNames = (c.prerrequisitos || [])
                                .map(pId => cursos.find(cur => cur.id === pId)?.codigo_curso)
                                .filter(Boolean)
                                .join(', ')

                              return (
                                <div 
                                  key={c.id} 
                                  className="malla-curso-item"
                                  style={{ 
                                    padding: 10, 
                                    borderRadius: 6, 
                                    background: 'var(--bg-body, #ffffff)', 
                                    border: '1px solid var(--border-color, #edf2f7)',
                                    position: 'relative',
                                    boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                                  }}
                                >
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingRight: 60 }}>
                                    <div>
                                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted, #718096)', letterSpacing: '0.05em' }}>
                                        {c.codigo_curso}
                                      </span>
                                      <h4 style={{ fontSize: '0.875rem', fontWeight: 600, margin: '2px 0 4px 0', color: 'var(--text-color, #2d3748)' }}>
                                        {c.nombre_curso}
                                      </h4>
                                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                                        <span className="badge" style={{ fontSize: '0.7rem', background: '#edf2f7', color: '#4a5568', padding: '2px 6px', borderRadius: '4px' }}>
                                          {c.creditos} CR
                                        </span>
                                        <Badge value={c.es_obligatorio ? 'OBLIGATORIO' : 'ELECTIVO'} />
                                      </div>
                                      {prereqNames && (
                                        <p style={{ fontSize: '0.7rem', color: '#dd6b20', marginTop: 4, margin: '4px 0 0 0', fontWeight: 550 }}>
                                          Prereq: {prereqNames}
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                  <button
                                    id={`btn-quitar-curso-${c.id}`}
                                    className="btn btn-danger btn-sm"
                                    style={{ 
                                      position: 'absolute', 
                                      right: 8, 
                                      top: 8, 
                                      padding: '2px 6px',
                                      fontSize: '0.75rem',
                                      border: 'none',
                                      lineHeight: '1.2'
                                    }}
                                    disabled={selectedPlanForMalla.estado === 'ACTIVO'}
                                    onClick={() => desasociarCurso(c.id)}
                                    title="Quitar curso de la malla"
                                  >
                                    Quitar
                                  </button>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>

                      <button
                        id={`btn-asignar-curso-ciclo-${ciclo}`}
                        className="btn btn-primary btn-sm"
                        style={{ width: '100%', marginTop: 8 }}
                        disabled={selectedPlanForMalla.estado === 'ACTIVO'}
                        onClick={() => {
                          setAsociarCiclo(ciclo)
                          setAsociarForm({ id_curso: '', es_obligatorio: true })
                          setShowAsociarModal(true)
                        }}
                      >
                        + Asignar Curso
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            <DataTable
              title="Planes de Estudio"
              columns={planesColumns}
              data={planes}
              loading={loading}
              onAdd={() => openModal('plan')}
              addLabel="Nuevo Plan"
              actions={row => (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    id={`btn-malla-plan-${row.id}`}
                    className="btn btn-secondary btn-sm"
                    onClick={() => gestionarMalla(row)}
                  >
                    Gestionar Malla
                  </button>
                  {row.estado === 'BORRADOR' && (
                    <button
                      id={`btn-activar-plan-${row.id}`}
                      className="btn btn-primary btn-sm"
                      onClick={() => activarPlan(row.id)}
                    >
                      Activar Plan
                    </button>
                  )}
                </div>
              )}
            />
          )
        )}

        {activeTab === 1 && (
          <DataTable
            title="Catálogo de Cursos"
            columns={cursosColumns}
            data={cursos}
            loading={loading}
            onAdd={() => openModal('curso')}
            addLabel="Nuevo Curso"
          />
        )}

        {activeTab === 2 && (
          <DataTable
            title="Secciones del Período"
            columns={seccionesColumns}
            data={secciones}
            loading={loading}
            onAdd={() => openModal('seccion')}
            addLabel="Nueva Sección"
          />
        )}

        {showModal && (
          <Modal
            title={
              modalType === 'plan' ? 'Nuevo Plan de Estudios' :
              modalType === 'curso' ? 'Nuevo Curso' : 'Nueva Sección'
            }
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-oferta" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Guardando...' : 'Crear'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            {modalType === 'plan' && (
              <>
                <div className="form-group">
                  <label className="form-label" htmlFor="plan-carrera">Carrera</label>
                  <input id="plan-carrera" className="form-input" value={form.carrera || ''} onChange={e => setForm({ ...form, carrera: e.target.value })} required />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="plan-version">Versión del Plan</label>
                    <input id="plan-version" className="form-input" value={form.version_plan || ''} onChange={e => setForm({ ...form, version_plan: e.target.value })} placeholder="ej: 2024" required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="plan-creditos">Créditos Totales</label>
                    <input id="plan-creditos" type="number" className="form-input" value={form.creditos_totales || ''} onChange={e => setForm({ ...form, creditos_totales: parseInt(e.target.value) })} required />
                  </div>
                </div>
              </>
            )}
            {modalType === 'curso' && (
              <>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-codigo">Código del Curso</label>
                    <input id="curso-codigo" className="form-input" value={form.codigo_curso || ''} onChange={e => setForm({ ...form, codigo_curso: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-creditos">Créditos</label>
                    <input id="curso-creditos" type="number" className="form-input" value={form.creditos || ''} onChange={e => setForm({ ...form, creditos: parseInt(e.target.value) })} required />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="curso-nombre">Nombre del Curso</label>
                  <input id="curso-nombre" className="form-input" value={form.nombre_curso || ''} onChange={e => setForm({ ...form, nombre_curso: e.target.value })} required />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-tipo">Tipo</label>
                    <select id="curso-tipo" className="form-select" value={form.tipo_curso || ''} onChange={e => setForm({ ...form, tipo_curso: e.target.value })}>
                      <option value="">Selecciona...</option>
                      <option value="OBLIGATORIO">OBLIGATORIO</option>
                      <option value="ELECTIVO">ELECTIVO</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-ciclo">Ciclo Sugerido</label>
                    <input id="curso-ciclo" type="number" className="form-input" value={form.ciclo_sugerido || ''} onChange={e => setForm({ ...form, ciclo_sugerido: parseInt(e.target.value) })} />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Prerrequisitos (Selección Múltiple)</label>
                  <div 
                    id="curso-prerrequisitos-list"
                    style={{ 
                      maxHeight: '140px', 
                      overflowY: 'auto', 
                      border: '1px solid var(--border-color, #e2e8f0)', 
                      padding: '10px', 
                      borderRadius: '6px',
                      background: 'var(--bg-body, #ffffff)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    {cursos.length === 0 ? (
                      <p style={{ fontStyle: 'italic', color: 'var(--text-muted, #718096)', fontSize: '0.875rem' }}>
                        No hay otros cursos en el catálogo para seleccionar como prerrequisitos.
                      </p>
                    ) : (
                      cursos.map(c => (
                        <label key={c.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.875rem' }}>
                          <input 
                            type="checkbox" 
                            checked={selectedPrereqs.includes(c.id)}
                            onChange={() => handlePrereqChange(c.id)}
                          />
                          <span>{c.codigo_curso} — {c.nombre_curso}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
            {modalType === 'seccion' && (
              <>
                <div className="form-group">
                  <label className="form-label" htmlFor="sec-curso">Seleccionar Curso</label>
                  <select id="sec-curso" className="form-select" value={form.id_curso || ''} onChange={e => setForm({ ...form, id_curso: e.target.value })}>
                    <option value="">Selecciona un curso...</option>
                    {cursos.map(c => <option key={c.id} value={c.id}>{c.codigo_curso} — {c.nombre_curso}</option>)}
                  </select>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="sec-codigo">Código de Sección</label>
                    <input id="sec-codigo" className="form-input" value={form.codigo_seccion || ''} onChange={e => setForm({ ...form, codigo_seccion: e.target.value })} placeholder="ej: A" required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="sec-vacantes">Vacantes Máximas</label>
                    <input id="sec-vacantes" type="number" className="form-input" value={form.vacantes_maximas || ''} onChange={e => setForm({ ...form, vacantes_maximas: parseInt(e.target.value) })} required />
                  </div>
                </div>
              </>
            )}
          </Modal>
        )}

        {showAsociarModal && (
          <Modal
            title={`Asignar Curso a Ciclo ${asociarCiclo}`}
            onClose={() => setShowAsociarModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowAsociarModal(false)}>Cancelar</button>
                <button id="btn-save-asociacion" className="btn btn-primary" onClick={handleAsociarCurso}>
                  Asignar
                </button>
              </>
            }
          >
            <div className="form-group">
              <label className="form-label" htmlFor="asociar-curso-select">Seleccionar Curso</label>
              <select 
                id="asociar-curso-select" 
                className="form-select" 
                value={asociarForm.id_curso} 
                onChange={e => setAsociarForm({ ...asociarForm, id_curso: e.target.value })}
              >
                <option value="">Selecciona un curso del catálogo...</option>
                {cursos
                  .filter(c => !cursosPlan.some(cp => cp.id === c.id))
                  .map(c => (
                    <option key={c.id} value={c.id}>
                      {c.codigo_curso} — {c.nombre_curso}
                    </option>
                  ))
                }
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="asociar-tipo-select">Condición del Curso en este Plan</label>
              <select 
                id="asociar-tipo-select" 
                className="form-select" 
                value={asociarForm.es_obligatorio ? 'true' : 'false'} 
                onChange={e => setAsociarForm({ ...asociarForm, es_obligatorio: e.target.value === 'true' })}
              >
                <option value="true">Obligatorio</option>
                <option value="false">Electivo</option>
              </select>
            </div>
          </Modal>
        )}
      </div>
    </Layout>
  )
}

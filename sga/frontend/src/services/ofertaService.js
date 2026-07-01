import api from './api'

export const ofertaService = {
  // Planes de estudio
  listarPlanes: () => api.get('/oferta/planes-estudio').then(r => r.data),
  crearPlan: (data) => api.post('/oferta/planes-estudio', data).then(r => r.data),
  activarPlan: (planId) => api.put(`/oferta/planes-estudio/${planId}/activar`).then(r => r.data),

  // Cursos
  listarCursos: () => api.get('/oferta/cursos').then(r => r.data),
  crearCurso: (data) => api.post('/oferta/cursos', data).then(r => r.data),

  // Cursos en un plan
  listarCursosPlan: (planId) => api.get(`/oferta/planes-estudio/${planId}/cursos`).then(r => r.data),
  asociarCursoAPlan: (planId, data) => api.post(`/oferta/planes-estudio/${planId}/cursos`, data).then(r => r.data),
  desasociarCursoDePlan: (planId, cursoId) => api.delete(`/oferta/planes-estudio/${planId}/cursos/${cursoId}`).then(r => r.data),

  // Prerrequisitos
  configurarPrerequisito: (cursoId, data) => api.post(`/oferta/cursos/${cursoId}/prerrequisitos`, data).then(r => r.data),

  // Secciones
  listarSecciones: (periodoId) => api.get(`/oferta/periodos/${periodoId}/secciones`).then(r => r.data),
  crearSeccion: (data) => api.post('/oferta/secciones', data).then(r => r.data),

  // Docentes en sección
  asignarDocente: (seccionId, data) => api.post(`/oferta/secciones/${seccionId}/docentes`, data).then(r => r.data),

  // Componentes de evaluación
  listarComponentes: (seccionId) => api.get(`/oferta/secciones/${seccionId}/componentes`).then(r => r.data),
  crearComponente: (seccionId, data) => api.post(`/oferta/secciones/${seccionId}/componentes`, data).then(r => r.data),
}

import api from './api'

export const matriculaService = {
  crear: (data) => api.post('/matriculas', data).then(r => r.data),
  listar: (alumnoId) => api.get('/matriculas', { params: { alumno_id: alumnoId } }).then(r => r.data),

  inscribir: (matriculaId, seccionId) =>
    api.post(`/matriculas/${matriculaId}/inscripciones`, { id_seccion: seccionId }).then(r => r.data),

  listarInscripciones: (matriculaId) =>
    api.get(`/matriculas/${matriculaId}/inscripciones`).then(r => r.data),

  retirar: (inscripcionId, motivo) =>
    api.post(`/inscripciones/${inscripcionId}/retiro`, { motivo }).then(r => r.data),
}

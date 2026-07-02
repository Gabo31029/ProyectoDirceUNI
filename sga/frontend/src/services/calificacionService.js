import api from './api'

export const calificacionService = {
  registrar: (seccionId, evaluacionId, calificaciones) =>
    api.post(`/calificaciones/secciones/${seccionId}/evaluaciones/${evaluacionId}`, { calificaciones }).then(r => r.data),

  publicar: (seccionId, evaluacionId) =>
    api.put(`/calificaciones/secciones/${seccionId}/evaluaciones/${evaluacionId}/publicar`).then(r => r.data),

  corregir: (calificacionId, valor_nuevo, justificacion) =>
    api.post(`/calificaciones/${calificacionId}/corregir`, { valor_nuevo, justificacion }).then(r => r.data),
}

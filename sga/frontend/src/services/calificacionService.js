import api from './api'

export const calificacionService = {
  registrar: (seccionId, componenteId, calificaciones) =>
    api.post(`/calificaciones/secciones/${seccionId}/componentes/${componenteId}`, { calificaciones }).then(r => r.data),

  publicar: (seccionId, componenteId) =>
    api.put(`/calificaciones/secciones/${seccionId}/componentes/${componenteId}/publicar`).then(r => r.data),

  corregir: (calificacionId, valor_nuevo, justificacion) =>
    api.post(`/calificaciones/${calificacionId}/corregir`, { valor_nuevo, justificacion }).then(r => r.data),
}

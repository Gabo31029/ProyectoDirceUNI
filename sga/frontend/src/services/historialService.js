import api from './api'

export const historialService = {
  obtener: (alumnoId) =>
    api.get(`/historial/alumnos/${alumnoId}`).then(r => r.data),

  descargarPDF: async (alumnoId) => {
    const response = await api.get(`/historial/alumnos/${alumnoId}/pdf`, {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `record_notas_${alumnoId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

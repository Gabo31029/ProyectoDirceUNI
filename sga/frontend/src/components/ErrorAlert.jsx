export default function ErrorAlert({ message, onClose }) {
  if (!message) return null
  return (
    <div className="alert alert-error" role="alert">
      <span>⚠️</span>
      <span style={{ flex: 1 }}>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem' }}
          aria-label="Cerrar alerta"
        >
          ×
        </button>
      )}
    </div>
  )
}

export function SuccessAlert({ message, onClose }) {
  if (!message) return null
  return (
    <div className="alert alert-success" role="alert">
      <span>✅</span>
      <span style={{ flex: 1 }}>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem' }}
          aria-label="Cerrar alerta"
        >
          ×
        </button>
      )}
    </div>
  )
}

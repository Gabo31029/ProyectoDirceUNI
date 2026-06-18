export default function ErrorAlert({ message, onClose }) {
  if (!message) return null
  return (
    <div className="banner banner-danger" role="alert" style={{ marginBottom: 16 }}>
      <span style={{ flex: 1 }}>⚠ {message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem', padding: 0 }}
          aria-label="Cerrar alerta"
        >×</button>
      )}
    </div>
  )
}

export function SuccessAlert({ message, onClose }) {
  if (!message) return null
  return (
    <div className="banner banner-success" role="alert" style={{ marginBottom: 16 }}>
      <span style={{ flex: 1 }}>✓ {message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem', padding: 0 }}
          aria-label="Cerrar alerta"
        >×</button>
      )}
    </div>
  )
}

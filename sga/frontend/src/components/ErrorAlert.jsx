import Icon from './Icon'

export default function ErrorAlert({ message, onClose }) {
  if (!message) return null

  let renderedMessage = message
  if (Array.isArray(message)) {
    renderedMessage = message.map((err) => {
      const field = err.loc ? err.loc[err.loc.length - 1] : ''
      return `${field ? field + ': ' : ''}${err.msg || JSON.stringify(err)}`
    }).join(' | ')
  } else if (typeof message === 'object') {
    renderedMessage = message.msg || message.detail || JSON.stringify(message)
  }

  return (
    <div className="banner banner-danger" role="alert" style={{ marginBottom: 16 }}>
      <Icon name="warning" size={15} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1 }}>{renderedMessage}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="iconbtn"
          aria-label="Cerrar alerta"
        >
          <Icon name="x" size={14} />
        </button>
      )}
    </div>
  )
}

export function SuccessAlert({ message, onClose }) {
  if (!message) return null
  return (
    <div className="banner banner-success" role="alert" style={{ marginBottom: 16 }}>
      <Icon name="check-circle" size={15} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1 }}>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="iconbtn"
          aria-label="Cerrar alerta"
        >
          <Icon name="x" size={14} />
        </button>
      )}
    </div>
  )
}

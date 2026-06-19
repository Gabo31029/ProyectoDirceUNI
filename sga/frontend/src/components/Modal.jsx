export default function Modal({ title, onClose, children, footer, size = '' }) {
  return (
    <div className="overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal${size === 'lg' ? ' lg' : ''}`} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-head" style={{ position: 'relative', paddingBottom: 16 }}>
          <h3 className="modal-title" id="modal-title">{title}</h3>
          <button className="iconbtn" onClick={onClose} aria-label="Cerrar">×</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
        {footer && (
          <div className="modal-foot">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

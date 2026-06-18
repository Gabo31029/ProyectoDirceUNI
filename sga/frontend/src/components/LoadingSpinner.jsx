export default function LoadingSpinner({ text = 'Cargando...' }) {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <span>{text}</span>
    </div>
  )
}

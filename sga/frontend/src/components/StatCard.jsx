export default function StatCard({ icon, label, value, colorClass = 'indigo' }) {
  return (
    <div className="stat-card">
      <div className={`stat-card-icon ${colorClass}`}>
        {icon}
      </div>
      <div className="stat-card-info">
        <div className="stat-card-label">{label}</div>
        <div className="stat-card-value">{value ?? '—'}</div>
      </div>
    </div>
  )
}

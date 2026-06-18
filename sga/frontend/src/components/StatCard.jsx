export default function StatCard({ icon, label, value, colorClass = 'blue' }) {
  return (
    <div className="stat">
      <div className="stat-top">
        <div className={`stat-ic ${colorClass}`}>{icon}</div>
      </div>
      <div>
        <div className="stat-val">{value ?? '—'}</div>
        <div className="stat-lbl">{label}</div>
      </div>
    </div>
  )
}

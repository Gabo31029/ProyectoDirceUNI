import { useState } from 'react'

export default function DataTable({ title, columns, data, actions, onAdd, addLabel = 'Nuevo', loading = false }) {
  const [search, setSearch] = useState('')

  const filtered = data.filter(row =>
    columns.some(col => {
      const val = col.accessor ? row[col.accessor] : ''
      return String(val ?? '').toLowerCase().includes(search.toLowerCase())
    })
  )

  return (
    <div className="table-container">
      <div className="table-header">
        <span className="table-title">{title} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({filtered.length})</span></span>
        <div className="flex items-center gap-3">
          <input
            className="table-search"
            placeholder="Buscar..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            aria-label="Buscar en tabla"
          />
          {onAdd && (
            <button id={`btn-add-${title?.replace(/\s/g, '-').toLowerCase()}`} className="btn btn-primary btn-sm" onClick={onAdd}>
              + {addLabel}
            </button>
          )}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="data-table" aria-label={title}>
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key || col.accessor}>{col.header}</th>
              ))}
              {actions && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  Cargando...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)}>
                  <div className="empty-state">
                    <span className="empty-state-icon">📭</span>
                    <span className="empty-state-title">Sin resultados</span>
                    <span className="empty-state-text">No hay datos para mostrar</span>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((row, i) => (
                <tr key={row.id || i}>
                  {columns.map(col => (
                    <td key={col.key || col.accessor} className={col.primary ? 'cell-primary' : ''}>
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                  {actions && (
                    <td>
                      <div className="table-actions">
                        {actions(row)}
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

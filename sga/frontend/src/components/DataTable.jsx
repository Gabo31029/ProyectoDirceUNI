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
    <div className="card card-flush">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--line)', gap: 14, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--ink)' }}>
          {title} <span style={{ color: 'var(--ink-3)', fontWeight: 400 }}>({filtered.length})</span>
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="search" style={{ height: 34 }}>
            <span style={{ fontSize: 13 }}>🔍</span>
            <input
              placeholder="Buscar…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              aria-label="Buscar en tabla"
            />
          </div>
          {onAdd && (
            <button
              id={`btn-add-${title?.replace(/\s/g, '-').toLowerCase()}`}
              className="btn btn-primary btn-sm"
              onClick={onAdd}
            >
              + {addLabel}
            </button>
          )}
        </div>
      </div>

      <div className="tbl-wrap">
        <table className="tbl" aria-label={title}>
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
                <td colSpan={columns.length + (actions ? 1 : 0)} style={{ textAlign: 'center', padding: '40px', color: 'var(--ink-3)' }}>
                  Cargando…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)}>
                  <div className="empty">
                    <div className="empty-ic">📭</div>
                    <div className="empty-title">Sin resultados</div>
                    <div className="empty-sub">No hay datos para mostrar</div>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((row, i) => (
                <tr key={row.id || i} className="zebra">
                  {columns.map(col => (
                    <td key={col.key || col.accessor} className={col.primary ? 'cell-strong' : ''}>
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                  {actions && (
                    <td>
                      <div className="row" style={{ gap: 8 }}>
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

import React from 'react'

/**
 * StatCard
 * Props:
 *   title  - string label
 *   value  - numeric/string value to display
 *   icon   - emoji or element
 *   color  - left border color (CSS color string)
 */
function StatCard({ title, value, icon, color }) {
  return (
    <div className="stat-card" style={{ borderLeftColor: color || '#1e3a5f' }}>
      <div className="stat-card-icon" style={{ color: color || '#1e3a5f' }}>
        {icon}
      </div>
      <div className="stat-card-content">
        <div className="stat-card-title">{title}</div>
        <div className="stat-card-value" style={{ color: color || '#1e3a5f' }}>
          {value !== undefined && value !== null ? value : '—'}
        </div>
      </div>
    </div>
  )
}

export default StatCard

import React, { useEffect, useState, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, LineChart, Line, ResponsiveContainer,
} from 'recharts'
import { getMostBorrowed, getCategoryWise, getMonthlyTrends, getOverdueAnalysis, runETL } from '../api/api'

const PIE_COLORS = [
  '#1e3a5f', '#2e86de', '#17a2b8', '#28a745', '#ffc107',
  '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c',
]

function Analytics() {
  const [mostBorrowed, setMostBorrowed]   = useState([])
  const [categoryData, setCategoryData]   = useState([])
  const [monthlyTrends, setMonthlyTrends] = useState([])
  const [overdueData, setOverdueData]     = useState([])
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState(null)
  const [etlLoading, setEtlLoading]       = useState(false)
  const [etlMsg, setEtlMsg]               = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [borrowedRes, catRes, trendsRes, overdueRes] = await Promise.all([
        getMostBorrowed(10),
        getCategoryWise(),
        getMonthlyTrends(12),
        getOverdueAnalysis(),
      ])

      // Most Borrowed
      const borrowed = Array.isArray(borrowedRes.data)
        ? borrowedRes.data
        : borrowedRes.data?.books || []
      setMostBorrowed(borrowed)

      // Category wise
      const cats = Array.isArray(catRes.data)
        ? catRes.data
        : catRes.data?.categories || []
      setCategoryData(cats)

      // Monthly trends — expect array of { month, borrows, returns } or similar
      const trends = Array.isArray(trendsRes.data)
        ? trendsRes.data
        : trendsRes.data?.trends || trendsRes.data?.monthly || []
      setMonthlyTrends(trends)

      // Overdue
      const overdue = Array.isArray(overdueRes.data)
        ? overdueRes.data
        : overdueRes.data?.overdue || overdueRes.data?.transactions || []
      setOverdueData(overdue)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleRefresh = async () => {
    setEtlLoading(true)
    setEtlMsg(null)
    try {
      const res = await runETL()
      const d = res.data
      setEtlMsg(
        `ETL complete — Books: ${d.books_loaded ?? d.books ?? '?'}, ` +
        `Borrowers: ${d.borrowers_loaded ?? d.borrowers ?? '?'}, ` +
        `Transactions: ${d.transactions_loaded ?? d.transactions ?? '?'}`
      )
      await fetchAll()
    } catch (err) {
      setEtlMsg('ETL failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setEtlLoading(false)
    }
  }

  const formatDate = (d) => {
    if (!d) return '—'
    try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }
    catch { return d }
  }

  // Prepare most-borrowed chart data
  const mostBorrowedChart = mostBorrowed.map((b) => ({
    name: b.title
      ? (b.title.length > 25 ? b.title.slice(0, 23) + '…' : b.title)
      : b.book_title || 'Unknown',
    Borrows: b.borrow_count ?? b.total_borrows ?? 0,
  }))

  // Pie chart data
  const pieData = categoryData.map((c) => ({
    name: c.category || c.name || 'Other',
    value: c.borrow_count ?? c.total_borrows ?? c.count ?? 0,
  }))

  // Monthly trends chart data — normalize keys
  const trendsChart = monthlyTrends.map((m) => ({
    month: m.month_label || m.month || m.period || '',
    Borrows: m.borrows ?? m.borrow_count ?? m.total_borrows ?? 0,
    Returns: m.returns ?? m.return_count ?? m.total_returns ?? 0,
  }))

  // Sort overdue by days_overdue desc
  const sortedOverdue = [...overdueData].sort(
    (a, b) => (b.days_overdue ?? 0) - (a.days_overdue ?? 0)
  )
  const totalFines = sortedOverdue.reduce((sum, o) => sum + (Number(o.fine_amount) || 0), 0)

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Loading analytics…
      </div>
    )
  }

  if (error) {
    return <div className="error-state">⚠ {error}</div>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">ETL Pipeline — Library borrowing insights</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRefresh}
          disabled={etlLoading}
        >
          {etlLoading ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
              Refreshing…
            </>
          ) : (
            '⟳ Refresh Analytics'
          )}
        </button>
      </div>

      {etlMsg && (
        <div className={`alert ${etlMsg.startsWith('ETL failed') ? 'alert-danger' : 'alert-success'}`}>
          {etlMsg}
        </div>
      )}

      {/* Row 1: Most Borrowed + Category Pie */}
      <div className="analytics-grid">
        {/* Most Borrowed — Horizontal Bar */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Top 10 Most Borrowed Books</h3>
          </div>
          {mostBorrowedChart.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <div className="empty-state-text">No data available</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={340}>
              <BarChart
                data={mostBorrowedChart}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#edf2f7" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 11, fill: '#718096' }}
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#4a5568' }}
                  width={140}
                />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
                />
                <Bar dataKey="Borrows" fill="#1e3a5f" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Category Pie */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Category-wise Borrowing Distribution</h3>
          </div>
          {pieData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🥧</div>
              <div className="empty-state-text">No data available</div>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={85}
                    dataKey="value"
                    paddingAngle={2}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => [value + ' borrows', name]}
                    contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
                  />
                  <Legend
                    formatter={(value) => (
                      <span style={{ fontSize: 12, color: '#4a5568' }}>{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Category table */}
              <div className="table-wrapper" style={{ marginTop: 12 }}>
                <table>
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th style={{ textAlign: 'right' }}>Total Borrows</th>
                      <th style={{ textAlign: 'right' }}>Unique Books</th>
                      <th style={{ textAlign: 'right' }}>Unique Borrowers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryData.map((c, i) => (
                      <tr key={i}>
                        <td>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span
                              style={{
                                display: 'inline-block',
                                width: 10,
                                height: 10,
                                borderRadius: '50%',
                                background: PIE_COLORS[i % PIE_COLORS.length],
                                flexShrink: 0,
                              }}
                            />
                            {c.category || c.name || 'Other'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 500 }}>
                          {c.borrow_count ?? c.total_borrows ?? c.count ?? 0}
                        </td>
                        <td style={{ textAlign: 'right', color: '#718096' }}>
                          {c.unique_books ?? c.book_count ?? '—'}
                        </td>
                        <td style={{ textAlign: 'right', color: '#718096' }}>
                          {c.unique_borrowers ?? c.borrower_count ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Row 2: Monthly Trends */}
      <div className="analytics-full-row">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Monthly Borrowing Trends (Last 12 Months)</h3>
          </div>
          {trendsChart.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📈</div>
              <div className="empty-state-text">No trend data available</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart
                data={trendsChart}
                margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#edf2f7" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: '#718096' }}
                  angle={-20}
                  textAnchor="end"
                  height={50}
                />
                <YAxis tick={{ fontSize: 11, fill: '#718096' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
                />
                <Legend
                  formatter={(value) => (
                    <span style={{ fontSize: 12, color: '#4a5568' }}>{value}</span>
                  )}
                />
                <Line
                  type="monotone"
                  dataKey="Borrows"
                  stroke="#1e3a5f"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#1e3a5f' }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="Returns"
                  stroke="#28a745"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#28a745' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Row 3: Overdue Analysis */}
      <div className="analytics-full-row">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Overdue Analysis</h3>
          </div>

          {/* Summary chips */}
          <div className="summary-row">
            <div className="summary-chip">
              Total Overdue: <strong>{sortedOverdue.length}</strong>
            </div>
            <div className="summary-chip">
              Total Fines: <strong style={{ color: '#dc3545' }}>₹{totalFines.toFixed(2)}</strong>
            </div>
          </div>

          {sortedOverdue.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">✅</div>
              <div className="empty-state-text">No overdue transactions — great job!</div>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Book Title</th>
                    <th>Borrower Name</th>
                    <th>Due Date</th>
                    <th style={{ textAlign: 'right' }}>Days Overdue</th>
                    <th style={{ textAlign: 'right' }}>Fine Amount (Rs.)</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedOverdue.map((o, idx) => (
                    <tr key={o.id ?? idx}>
                      <td style={{ color: '#a0aec0', fontSize: 12 }}>{idx + 1}</td>
                      <td style={{ fontWeight: 500 }}>
                        {o.book_title || o.book?.title || `Book #${o.book_id}`}
                      </td>
                      <td style={{ color: '#4a5568' }}>
                        {o.borrower_name || o.borrower?.name || `Borrower #${o.borrower_id}`}
                      </td>
                      <td style={{ color: '#718096', whiteSpace: 'nowrap' }}>
                        {formatDate(o.due_date)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="badge badge-danger">
                          {o.days_overdue != null ? `${o.days_overdue}d` : '—'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: '#dc3545' }}>
                        {o.fine_amount != null
                          ? `₹${Number(o.fine_amount).toFixed(2)}`
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Analytics

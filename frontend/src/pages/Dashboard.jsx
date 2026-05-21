import React, { useEffect, useState, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts'
import StatCard from '../components/StatCard'
import {
  getDashboardStats,
  getMostBorrowed,
  getCategoryWise,
  runETL,
} from '../api/api'

const PIE_COLORS = [
  '#1e3a5f', '#2e86de', '#17a2b8', '#28a745', '#ffc107',
  '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c',
]

function Dashboard() {
  const [stats, setStats]           = useState(null)
  const [mostBorrowed, setMostBorrowed] = useState([])
  const [categoryData, setCategoryData] = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [etlLoading, setEtlLoading] = useState(false)
  const [etlResult, setEtlResult]   = useState(null)
  const [etlError, setEtlError]     = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, borrowedRes, categoryRes] = await Promise.all([
        getDashboardStats(),
        getMostBorrowed(5),
        getCategoryWise(),
      ])
      setStats(statsRes.data)
      // Most borrowed: array of { title, borrow_count } or similar
      const borrowed = Array.isArray(borrowedRes.data)
        ? borrowedRes.data
        : borrowedRes.data?.books || []
      setMostBorrowed(borrowed.slice(0, 5))
      // Category wise: array of { category, borrow_count } or similar
      const cats = Array.isArray(categoryRes.data)
        ? categoryRes.data
        : categoryRes.data?.categories || []
      setCategoryData(cats)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleRunETL = async () => {
    setEtlLoading(true)
    setEtlError(null)
    setEtlResult(null)
    try {
      const res = await runETL()
      setEtlResult(res.data)
      // Refresh dashboard after ETL
      await fetchAll()
    } catch (err) {
      setEtlError(err?.response?.data?.detail || err.message || 'ETL pipeline failed')
    } finally {
      setEtlLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Loading dashboard…
      </div>
    )
  }

  if (error) {
    return <div className="error-state">⚠ {error}</div>
  }

  const topBookData = mostBorrowed.map((b) => ({
    name: b.title ? (b.title.length > 20 ? b.title.slice(0, 18) + '…' : b.title) : b.book_title || 'Unknown',
    Borrows: b.borrow_count ?? b.total_borrows ?? 0,
  }))

  const pieData = categoryData.map((c) => ({
    name: c.category || c.name || 'Other',
    value: c.borrow_count ?? c.total_borrows ?? c.count ?? 0,
  }))

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Library Management System — Overview</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRunETL}
          disabled={etlLoading}
        >
          {etlLoading ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
              Running ETL…
            </>
          ) : (
            '⚙ Run ETL Pipeline'
          )}
        </button>
      </div>

      {/* ETL Alerts */}
      {etlError && (
        <div className="alert alert-danger">⚠ ETL Error: {etlError}</div>
      )}
      {etlResult && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h3 className="card-title">✅ ETL Pipeline Completed</h3>
          </div>
          <div className="etl-result">
            <div className="etl-stat">
              <div className="etl-stat-value">{etlResult.books_loaded ?? etlResult.books ?? '—'}</div>
              <div className="etl-stat-label">Books Loaded</div>
            </div>
            <div className="etl-stat">
              <div className="etl-stat-value">{etlResult.borrowers_loaded ?? etlResult.borrowers ?? '—'}</div>
              <div className="etl-stat-label">Borrowers Loaded</div>
            </div>
            <div className="etl-stat">
              <div className="etl-stat-value">{etlResult.transactions_loaded ?? etlResult.transactions ?? '—'}</div>
              <div className="etl-stat-label">Transactions Loaded</div>
            </div>
            {etlResult.status && (
              <div className="etl-stat">
                <div className="etl-stat-value" style={{ fontSize: 14 }}>{etlResult.status}</div>
                <div className="etl-stat-label">Status</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="stat-cards-grid">
        <StatCard
          title="Total Books"
          value={stats?.total_books ?? stats?.books ?? '—'}
          icon="📖"
          color="#1e3a5f"
        />
        <StatCard
          title="Total Borrowers"
          value={stats?.total_borrowers ?? stats?.borrowers ?? '—'}
          icon="👥"
          color="#17a2b8"
        />
        <StatCard
          title="Active Borrows"
          value={stats?.active_borrows ?? stats?.active_transactions ?? '—'}
          icon="🔄"
          color="#28a745"
        />
        <StatCard
          title="Overdue Books"
          value={stats?.overdue_count ?? stats?.overdue_books ?? stats?.overdue ?? '—'}
          icon="⚠️"
          color="#dc3545"
        />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Bar Chart — Top 5 Most Borrowed */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Top 5 Most Borrowed Books</h3>
          </div>
          {topBookData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <div className="empty-state-text">No borrowing data available</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={topBookData} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#edf2f7" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#718096' }}
                  angle={-30}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11, fill: '#718096' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
                />
                <Bar dataKey="Borrows" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie Chart — Category-wise */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Category-wise Borrowing</h3>
          </div>
          {pieData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🥧</div>
              <div className="empty-state-text">No category data available</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="45%"
                  outerRadius={90}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} (${(percent * 100).toFixed(0)}%)`
                  }
                  labelLine={false}
                >
                  {pieData.map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [value, name]}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
                />
                <Legend
                  formatter={(value) => (
                    <span style={{ fontSize: 12, color: '#4a5568' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

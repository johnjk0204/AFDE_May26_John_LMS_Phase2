import React, { useEffect, useState, useCallback } from 'react'
import { getTransactions, borrowBook, returnBook, getBooks, getBorrowers } from '../api/api'

const STATUS_BADGE = {
  active:   'badge-primary',
  returned: 'badge-success',
  overdue:  'badge-danger',
}

const TABS = ['all', 'active', 'returned', 'overdue']

function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)
  const [activeTab, setActiveTab]       = useState('all')
  const [showModal, setShowModal]       = useState(false)
  const [books, setBooks]               = useState([])
  const [borrowers, setBorrowers]       = useState([])
  const [form, setForm]                 = useState({ book_id: '', borrower_id: '', borrow_date: '' })
  const [formErrors, setFormErrors]     = useState({})
  const [saving, setSaving]             = useState(false)
  const [saveError, setSaveError]       = useState(null)
  const [returningId, setReturningId]   = useState(null)

  const fetchTransactions = useCallback(async (status) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getTransactions(status === 'all' ? undefined : status)
      const data = Array.isArray(res.data) ? res.data : res.data?.transactions || []
      setTransactions(data)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTransactions(activeTab)
  }, [activeTab, fetchTransactions])

  const openBorrowModal = async () => {
    setForm({ book_id: '', borrower_id: '', borrow_date: new Date().toISOString().slice(0, 10) })
    setFormErrors({})
    setSaveError(null)
    setShowModal(true)
    // Load books and borrowers for dropdowns
    try {
      const [booksRes, borrowersRes] = await Promise.all([getBooks(), getBorrowers()])
      const bList = Array.isArray(booksRes.data) ? booksRes.data : booksRes.data?.books || []
      const brList = Array.isArray(borrowersRes.data) ? borrowersRes.data : borrowersRes.data?.borrowers || []
      setBooks(bList.filter((b) => b.available_copies > 0))
      setBorrowers(brList)
    } catch {
      // Use existing lists if any
    }
  }

  const closeModal = () => setShowModal(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (formErrors[name]) setFormErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  const validateBorrow = () => {
    const errors = {}
    if (!form.book_id)     errors.book_id     = 'Please select a book'
    if (!form.borrower_id) errors.borrower_id = 'Please select a borrower'
    if (!form.borrow_date) errors.borrow_date = 'Borrow date is required'
    return errors
  }

  const handleBorrowSubmit = async (e) => {
    e.preventDefault()
    const errors = validateBorrow()
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }
    setSaving(true)
    setSaveError(null)
    try {
      await borrowBook({
        book_id:     Number(form.book_id),
        borrower_id: Number(form.borrower_id),
        borrow_date: form.borrow_date,
      })
      closeModal()
      fetchTransactions(activeTab)
    } catch (err) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to create transaction')
    } finally {
      setSaving(false)
    }
  }

  const handleReturn = async (t) => {
    if (!window.confirm(`Return "${t.book_title || 'this book'}"?`)) return
    setReturningId(t.id)
    try {
      await returnBook(t.id)
      fetchTransactions(activeTab)
    } catch (err) {
      alert(err?.response?.data?.detail || err.message || 'Failed to return book')
    } finally {
      setReturningId(null)
    }
  }

  const formatDate = (d) => {
    if (!d) return '—'
    try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }
    catch { return d }
  }

  const tabLabel = (tab) => {
    if (tab === 'all') return `All (${transactions.length})`
    const count = tab === activeTab ? transactions.length : ''
    return tab.charAt(0).toUpperCase() + tab.slice(1) + (count ? ` (${count})` : '')
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Transactions</h1>
          <p className="page-subtitle">Track book borrowing and returns</p>
        </div>
        <button className="btn btn-success" onClick={openBorrowModal}>
          + Borrow Book
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`filter-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'all'
              ? 'All'
              : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="card">
        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            Loading transactions…
          </div>
        )}

        {error && !loading && <div className="error-state">⚠ {error}</div>}

        {!loading && !error && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Book Title</th>
                  <th>Borrower</th>
                  <th>Borrow Date</th>
                  <th>Due Date</th>
                  <th>Return Date</th>
                  <th>Status</th>
                  <th>Fine (Rs.)</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={9}>
                      <div className="empty-state">
                        <div className="empty-state-icon">📋</div>
                        <div className="empty-state-text">No transactions found</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  transactions.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: 12, color: '#a0aec0' }}>
                        #{t.id}
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: 200 }}>
                        {t.book_title || t.book?.title || `Book #${t.book_id}`}
                      </td>
                      <td style={{ color: '#4a5568' }}>
                        {t.borrower_name || t.borrower?.name || `Borrower #${t.borrower_id}`}
                      </td>
                      <td style={{ color: '#718096', whiteSpace: 'nowrap' }}>
                        {formatDate(t.borrow_date)}
                      </td>
                      <td style={{ color: '#718096', whiteSpace: 'nowrap' }}>
                        {formatDate(t.due_date)}
                      </td>
                      <td style={{ color: '#718096', whiteSpace: 'nowrap' }}>
                        {formatDate(t.return_date)}
                      </td>
                      <td>
                        <span className={`badge ${STATUS_BADGE[t.status] || 'badge-secondary'}`}>
                          {t.status ? t.status.charAt(0).toUpperCase() + t.status.slice(1) : '—'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {t.fine_amount != null && t.fine_amount > 0 ? (
                          <span style={{ color: '#dc3545', fontWeight: 600 }}>
                            ₹{Number(t.fine_amount).toFixed(2)}
                          </span>
                        ) : (
                          <span style={{ color: '#a0aec0' }}>—</span>
                        )}
                      </td>
                      <td>
                        {(t.status === 'active' || t.status === 'overdue') && (
                          <button
                            className="btn btn-success btn-sm"
                            onClick={() => handleReturn(t)}
                            disabled={returningId === t.id}
                          >
                            {returningId === t.id ? (
                              <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                            ) : (
                              '↩ Return'
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Borrow Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Borrow a Book</h2>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>
            <form onSubmit={handleBorrowSubmit}>
              <div className="modal-body">
                {saveError && <div className="alert alert-danger">⚠ {saveError}</div>}

                <div className="form-group">
                  <label className="form-label">Book *</label>
                  <select
                    className={`form-control ${formErrors.book_id ? 'error' : ''}`}
                    name="book_id"
                    value={form.book_id}
                    onChange={handleChange}
                  >
                    <option value="">Select available book…</option>
                    {books.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.title} — {b.author} ({b.available_copies} available)
                      </option>
                    ))}
                  </select>
                  {formErrors.book_id && <div className="form-error">{formErrors.book_id}</div>}
                </div>

                <div className="form-group">
                  <label className="form-label">Borrower *</label>
                  <select
                    className={`form-control ${formErrors.borrower_id ? 'error' : ''}`}
                    name="borrower_id"
                    value={form.borrower_id}
                    onChange={handleChange}
                  >
                    <option value="">Select borrower…</option>
                    {borrowers.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} — {b.email}
                      </option>
                    ))}
                  </select>
                  {formErrors.borrower_id && <div className="form-error">{formErrors.borrower_id}</div>}
                </div>

                <div className="form-group">
                  <label className="form-label">Borrow Date *</label>
                  <input
                    className={`form-control ${formErrors.borrow_date ? 'error' : ''}`}
                    name="borrow_date"
                    type="date"
                    value={form.borrow_date}
                    onChange={handleChange}
                  />
                  {formErrors.borrow_date && <div className="form-error">{formErrors.borrow_date}</div>}
                </div>

                <div className="alert alert-info">
                  ℹ The due date will be set automatically (typically 14 days from borrow date).
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-success" disabled={saving}>
                  {saving ? (
                    <>
                      <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                      Processing…
                    </>
                  ) : (
                    'Confirm Borrow'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Transactions

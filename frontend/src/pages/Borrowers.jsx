import React, { useEffect, useState, useCallback } from 'react'
import { getBorrowers, createBorrower, updateBorrower, deleteBorrower } from '../api/api'

const MEMBERSHIP_TYPES = ['basic', 'premium', 'student']

const MEMBERSHIP_BADGE = {
  basic:   'badge-secondary',
  premium: 'badge-gold',
  student: 'badge-primary',
}

const EMPTY_FORM = {
  name: '',
  email: '',
  phone: '',
  membership_date: '',
  membership_type: 'basic',
  address: '',
}

function validate(form) {
  const errors = {}
  if (!form.name.trim())  errors.name  = 'Name is required'
  if (!form.email.trim()) errors.email = 'Email is required'
  if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = 'Invalid email address'
  if (!form.membership_type) errors.membership_type = 'Membership type is required'
  return errors
}

function Borrowers() {
  const [borrowers, setBorrowers]   = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [search, setSearch]         = useState('')
  const [showModal, setShowModal]   = useState(false)
  const [editing, setEditing]       = useState(null)
  const [form, setForm]             = useState(EMPTY_FORM)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving]         = useState(false)
  const [saveError, setSaveError]   = useState(null)

  const fetchBorrowers = useCallback(async (q) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getBorrowers(q || undefined)
      const data = Array.isArray(res.data) ? res.data : res.data?.borrowers || []
      setBorrowers(data)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load borrowers')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBorrowers()
  }, [fetchBorrowers])

  useEffect(() => {
    const t = setTimeout(() => fetchBorrowers(search), 350)
    return () => clearTimeout(t)
  }, [search, fetchBorrowers])

  const openAdd = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormErrors({})
    setSaveError(null)
    setShowModal(true)
  }

  const openEdit = (b) => {
    setEditing(b)
    setForm({
      name:            b.name || '',
      email:           b.email || '',
      phone:           b.phone || '',
      membership_date: b.membership_date ? b.membership_date.slice(0, 10) : '',
      membership_type: b.membership_type || 'basic',
      address:         b.address || '',
    })
    setFormErrors({})
    setSaveError(null)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditing(null)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (formErrors[name]) setFormErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errors = validate(form)
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }
    setSaving(true)
    setSaveError(null)
    try {
      if (editing) {
        await updateBorrower(editing.id, form)
      } else {
        await createBorrower(form)
      }
      closeModal()
      fetchBorrowers(search)
    } catch (err) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to save borrower')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (b) => {
    if (!window.confirm(`Delete borrower "${b.name}"? This cannot be undone.`)) return
    try {
      await deleteBorrower(b.id)
      fetchBorrowers(search)
    } catch (err) {
      alert(err?.response?.data?.detail || err.message || 'Failed to delete borrower')
    }
  }

  const formatDate = (d) => {
    if (!d) return '—'
    try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }
    catch { return d }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Borrowers</h1>
          <p className="page-subtitle">Manage library members and memberships</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>
          + Add Borrower
        </button>
      </div>

      <div className="card">
        <div className="search-bar">
          <input
            className="search-input"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {loading && <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />}
          <span style={{ color: '#718096', fontSize: 13, marginLeft: 'auto' }}>
            {borrowers.length} borrower{borrowers.length !== 1 ? 's' : ''}
          </span>
        </div>

        {error && <div className="error-state">⚠ {error}</div>}

        {!error && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Membership Date</th>
                  <th>Membership Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {borrowers.length === 0 && !loading ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty-state">
                        <div className="empty-state-icon">👤</div>
                        <div className="empty-state-text">No borrowers found</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  borrowers.map((b, idx) => (
                    <tr key={b.id}>
                      <td style={{ color: '#a0aec0', fontSize: 12 }}>{idx + 1}</td>
                      <td style={{ fontWeight: 500 }}>{b.name}</td>
                      <td style={{ color: '#4a5568' }}>{b.email}</td>
                      <td style={{ color: '#718096' }}>{b.phone || '—'}</td>
                      <td style={{ color: '#718096' }}>{formatDate(b.membership_date)}</td>
                      <td>
                        <span className={`badge ${MEMBERSHIP_BADGE[b.membership_type] || 'badge-secondary'}`}>
                          {b.membership_type
                            ? b.membership_type.charAt(0).toUpperCase() + b.membership_type.slice(1)
                            : '—'}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-outline btn-sm" onClick={() => openEdit(b)}>
                            ✏ Edit
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(b)}>
                            🗑 Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{editing ? 'Edit Borrower' : 'Add New Borrower'}</h2>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                {saveError && <div className="alert alert-danger">⚠ {saveError}</div>}

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Name *</label>
                    <input
                      className={`form-control ${formErrors.name ? 'error' : ''}`}
                      name="name"
                      value={form.name}
                      onChange={handleChange}
                      placeholder="Full name"
                    />
                    {formErrors.name && <div className="form-error">{formErrors.name}</div>}
                  </div>

                  <div className="form-group">
                    <label className="form-label">Email *</label>
                    <input
                      className={`form-control ${formErrors.email ? 'error' : ''}`}
                      name="email"
                      type="email"
                      value={form.email}
                      onChange={handleChange}
                      placeholder="email@example.com"
                    />
                    {formErrors.email && <div className="form-error">{formErrors.email}</div>}
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Phone</label>
                    <input
                      className="form-control"
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="+91 98765 43210"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Membership Date</label>
                    <input
                      className="form-control"
                      name="membership_date"
                      type="date"
                      value={form.membership_date}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Membership Type *</label>
                  <select
                    className={`form-control ${formErrors.membership_type ? 'error' : ''}`}
                    name="membership_type"
                    value={form.membership_type}
                    onChange={handleChange}
                  >
                    {MEMBERSHIP_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </option>
                    ))}
                  </select>
                  {formErrors.membership_type && (
                    <div className="form-error">{formErrors.membership_type}</div>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label">Address</label>
                  <textarea
                    className="form-control"
                    name="address"
                    value={form.address}
                    onChange={handleChange}
                    placeholder="Street, City, State…"
                    rows={2}
                    style={{ resize: 'vertical' }}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? (
                    <>
                      <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                      Saving…
                    </>
                  ) : (
                    editing ? 'Save Changes' : 'Add Borrower'
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

export default Borrowers

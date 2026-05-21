import React, { useEffect, useState, useCallback } from 'react'
import { getBooks, createBook, updateBook, deleteBook } from '../api/api'

const CATEGORIES = [
  'Fiction',
  'Non-Fiction',
  'Science',
  'Technology',
  'History',
  'Biography',
  'Mystery',
  'Romance',
  'Self-Help',
  'Children',
]

const EMPTY_FORM = {
  title: '',
  author: '',
  category: '',
  isbn: '',
  publication_year: '',
  total_copies: '',
  available_copies: '',
  description: '',
}

function validate(form) {
  const errors = {}
  if (!form.title.trim())       errors.title  = 'Title is required'
  if (!form.author.trim())      errors.author = 'Author is required'
  if (!form.category)           errors.category = 'Category is required'
  if (!form.total_copies)       errors.total_copies = 'Total copies is required'
  if (!form.available_copies && form.available_copies !== 0)
    errors.available_copies = 'Available copies is required'
  if (
    form.total_copies &&
    form.available_copies &&
    Number(form.available_copies) > Number(form.total_copies)
  )
    errors.available_copies = 'Cannot exceed total copies'
  return errors
}

function Books() {
  const [books, setBooks]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [search, setSearch]       = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingBook, setEditingBook] = useState(null)
  const [form, setForm]           = useState(EMPTY_FORM)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving]       = useState(false)
  const [saveError, setSaveError] = useState(null)

  const fetchBooks = useCallback(async (q) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getBooks(q || undefined)
      const data = Array.isArray(res.data) ? res.data : res.data?.books || []
      setBooks(data)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load books')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBooks()
  }, [fetchBooks])

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => fetchBooks(search), 350)
    return () => clearTimeout(t)
  }, [search, fetchBooks])

  const openAdd = () => {
    setEditingBook(null)
    setForm(EMPTY_FORM)
    setFormErrors({})
    setSaveError(null)
    setShowModal(true)
  }

  const openEdit = (book) => {
    setEditingBook(book)
    setForm({
      title:            book.title || '',
      author:           book.author || '',
      category:         book.category || '',
      isbn:             book.isbn || '',
      publication_year: book.publication_year ? String(book.publication_year) : '',
      total_copies:     book.total_copies != null ? String(book.total_copies) : '',
      available_copies: book.available_copies != null ? String(book.available_copies) : '',
      description:      book.description || '',
    })
    setFormErrors({})
    setSaveError(null)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingBook(null)
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
      const payload = {
        ...form,
        publication_year: form.publication_year ? Number(form.publication_year) : null,
        total_copies:     Number(form.total_copies),
        available_copies: Number(form.available_copies),
      }
      if (editingBook) {
        await updateBook(editingBook.id, payload)
      } else {
        await createBook(payload)
      }
      closeModal()
      fetchBooks(search)
    } catch (err) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to save book')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (book) => {
    if (!window.confirm(`Delete "${book.title}"? This cannot be undone.`)) return
    try {
      await deleteBook(book.id)
      fetchBooks(search)
    } catch (err) {
      alert(err?.response?.data?.detail || err.message || 'Failed to delete book')
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Books</h1>
          <p className="page-subtitle">Manage your library book catalog</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>
          + Add Book
        </button>
      </div>

      <div className="card">
        <div className="search-bar">
          <input
            className="search-input"
            placeholder="Search by title, author, or category…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {loading && <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />}
          <span style={{ color: '#718096', fontSize: 13, marginLeft: 'auto' }}>
            {books.length} book{books.length !== 1 ? 's' : ''}
          </span>
        </div>

        {error && <div className="error-state">⚠ {error}</div>}

        {!error && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Category</th>
                  <th>ISBN</th>
                  <th>Year</th>
                  <th>Total</th>
                  <th>Available</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {books.length === 0 && !loading ? (
                  <tr>
                    <td colSpan={9}>
                      <div className="empty-state">
                        <div className="empty-state-icon">📚</div>
                        <div className="empty-state-text">No books found</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  books.map((book, idx) => (
                    <tr key={book.id}>
                      <td style={{ color: '#a0aec0', fontSize: 12 }}>{idx + 1}</td>
                      <td>
                        <div style={{ fontWeight: 500 }}>{book.title}</div>
                      </td>
                      <td style={{ color: '#4a5568' }}>{book.author}</td>
                      <td>
                        <span className="badge badge-info">{book.category}</span>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 12, color: '#718096' }}>
                        {book.isbn || '—'}
                      </td>
                      <td style={{ color: '#718096' }}>{book.publication_year || '—'}</td>
                      <td style={{ textAlign: 'center', fontWeight: 500 }}>{book.total_copies}</td>
                      <td style={{ textAlign: 'center' }}>
                        <span
                          className={`badge ${Number(book.available_copies) > 0 ? 'badge-success' : 'badge-danger'}`}
                        >
                          {book.available_copies}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => openEdit(book)}
                          >
                            ✏ Edit
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleDelete(book)}
                          >
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
              <h2 className="modal-title">{editingBook ? 'Edit Book' : 'Add New Book'}</h2>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                {saveError && <div className="alert alert-danger">⚠ {saveError}</div>}

                <div className="form-group">
                  <label className="form-label">Title *</label>
                  <input
                    className={`form-control ${formErrors.title ? 'error' : ''}`}
                    name="title"
                    value={form.title}
                    onChange={handleChange}
                    placeholder="Book title"
                  />
                  {formErrors.title && <div className="form-error">{formErrors.title}</div>}
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Author *</label>
                    <input
                      className={`form-control ${formErrors.author ? 'error' : ''}`}
                      name="author"
                      value={form.author}
                      onChange={handleChange}
                      placeholder="Author name"
                    />
                    {formErrors.author && <div className="form-error">{formErrors.author}</div>}
                  </div>

                  <div className="form-group">
                    <label className="form-label">Category *</label>
                    <select
                      className={`form-control ${formErrors.category ? 'error' : ''}`}
                      name="category"
                      value={form.category}
                      onChange={handleChange}
                    >
                      <option value="">Select category…</option>
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    {formErrors.category && <div className="form-error">{formErrors.category}</div>}
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">ISBN</label>
                    <input
                      className="form-control"
                      name="isbn"
                      value={form.isbn}
                      onChange={handleChange}
                      placeholder="978-xxx-xxx"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Publication Year</label>
                    <input
                      className="form-control"
                      name="publication_year"
                      type="number"
                      value={form.publication_year}
                      onChange={handleChange}
                      placeholder="e.g. 2023"
                      min="1000"
                      max="2100"
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Total Copies *</label>
                    <input
                      className={`form-control ${formErrors.total_copies ? 'error' : ''}`}
                      name="total_copies"
                      type="number"
                      value={form.total_copies}
                      onChange={handleChange}
                      placeholder="e.g. 5"
                      min="0"
                    />
                    {formErrors.total_copies && <div className="form-error">{formErrors.total_copies}</div>}
                  </div>

                  <div className="form-group">
                    <label className="form-label">Available Copies *</label>
                    <input
                      className={`form-control ${formErrors.available_copies ? 'error' : ''}`}
                      name="available_copies"
                      type="number"
                      value={form.available_copies}
                      onChange={handleChange}
                      placeholder="e.g. 3"
                      min="0"
                    />
                    {formErrors.available_copies && (
                      <div className="form-error">{formErrors.available_copies}</div>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="Short description…"
                    rows={3}
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
                    editingBook ? 'Save Changes' : 'Add Book'
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

export default Books

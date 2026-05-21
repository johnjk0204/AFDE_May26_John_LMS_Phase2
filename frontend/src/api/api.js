import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:1009',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===== BOOKS =====
export const getBooks = (search) =>
  api.get('/api/books', { params: search ? { search } : {} })

export const createBook = (data) =>
  api.post('/api/books', data)

export const updateBook = (id, data) =>
  api.put(`/api/books/${id}`, data)

export const deleteBook = (id) =>
  api.delete(`/api/books/${id}`)

// ===== BORROWERS =====
export const getBorrowers = (search) =>
  api.get('/api/borrowers', { params: search ? { search } : {} })

export const createBorrower = (data) =>
  api.post('/api/borrowers', data)

export const updateBorrower = (id, data) =>
  api.put(`/api/borrowers/${id}`, data)

export const deleteBorrower = (id) =>
  api.delete(`/api/borrowers/${id}`)

// ===== TRANSACTIONS =====
export const getTransactions = (status) =>
  api.get('/api/transactions', { params: status ? { status } : {} })

export const borrowBook = (data) =>
  api.post('/api/transactions', data)

export const returnBook = (id) =>
  api.put(`/api/transactions/${id}/return`)

// ===== ANALYTICS =====
export const getDashboardStats = () =>
  api.get('/api/analytics/dashboard')

export const getMostBorrowed = (limit = 10) =>
  api.get('/api/analytics/most-borrowed', { params: { limit } })

export const getCategoryWise = () =>
  api.get('/api/analytics/category-wise')

export const getMonthlyTrends = (months = 12) =>
  api.get('/api/analytics/monthly-trends', { params: { months } })

export const getOverdueAnalysis = () =>
  api.get('/api/analytics/overdue')

// ===== ETL =====
export const runETL = () =>
  api.post('/api/etl/run')

export default api

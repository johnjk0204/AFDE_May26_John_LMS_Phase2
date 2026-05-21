# Library Management System — Phase 2 (ETL Pipeline)

A full-stack Library Management System with an integrated ETL pipeline for transaction analytics and book usage reporting.

## Tech Stack

| Layer     | Technology                           |
|-----------|--------------------------------------|
| Backend   | Python 3.10+, FastAPI, SQLAlchemy, SQLite |
| ETL       | Python, Pandas                       |
| Frontend  | React 18, Vite, Recharts, Axios      |
| Dataset   | CSV files (70 books, 60 borrowers, 220 transactions) |

---

## Project Structure

```
library-management-system/
├── datasets/                   # Input CSV datasets
│   ├── books.csv               # 70 book records
│   ├── borrowers.csv           # 60 borrower records
│   ├── transactions.csv        # 220 transaction records
│   └── generate_data.py        # Dataset generation script
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # SQLAlchemy engine & session
│   ├── models.py               # ORM models (7 tables)
│   ├── schemas.py              # Pydantic v2 request/response schemas
│   ├── requirements.txt
│   ├── routers/
│   │   ├── books.py            # Books CRUD API
│   │   ├── borrowers.py        # Borrowers CRUD API
│   │   ├── transactions.py     # Borrow/return API
│   │   └── analytics.py        # Analytics endpoints
│   └── etl/
│       ├── extract.py          # Extract: read CSV files with pandas
│       ├── transform.py        # Transform: clean, deduplicate, compute
│       ├── load.py             # Load: upsert into SQLite analytics tables
│       └── pipeline.py         # Pipeline orchestrator
└── frontend/
    ├── src/
    │   ├── api/api.js          # Axios API client
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   └── StatCard.jsx
    │   └── pages/
    │       ├── Dashboard.jsx   # Summary + ETL trigger
    │       ├── Books.jsx       # Books CRUD
    │       ├── Borrowers.jsx   # Borrowers CRUD
    │       ├── Transactions.jsx# Borrow / return
    │       └── Analytics.jsx   # All charts & tables
    └── package.json
```

---

## ETL Workflow

The ETL pipeline runs automatically on server startup (if analytics tables are empty) and can be manually triggered via the dashboard.

### 1. Extract

`etl/extract.py` reads the three CSV files from the `datasets/` directory using pandas:

```python
books_df      = extract_books("datasets/books.csv")
borrowers_df  = extract_borrowers("datasets/borrowers.csv")
transactions_df = extract_transactions("datasets/transactions.csv")
```

### 2. Transform

`etl/transform.py` applies cleaning and enrichment:

| Step | What happens |
|------|-------------|
| **Books** | Drop duplicate ISBNs, fill missing descriptions, validate `available_copies ≤ total_copies` |
| **Borrowers** | Drop duplicate emails, validate email format, parse `membership_date` |
| **Transactions** | Drop duplicate IDs, parse date columns, recompute `status` (active/returned/overdue), recompute `fine_amount` (₹0.50/day overdue) |
| **Book Analytics** | Group by `book_id` → `total_borrows`, `avg_borrow_duration` |
| **Monthly Trends** | Group by `year`/`month` of `borrow_date` → `total_borrows`, `total_returns`, `overdue_count` |
| **Category Analytics** | Join transactions + books → group by `category` → `total_borrows`, `unique_books`, `unique_borrowers` |
| **Overdue Analytics** | Filter `status=overdue`, join with books and borrowers, compute `days_overdue` and `fine_amount` |

### 3. Load

`etl/load.py` writes cleaned data into SQLite:

- **Core tables** (`books`, `borrowers`, `transactions`): upsert by natural key (isbn, email, transaction_id)
- **Analytics tables** (`book_analytics`, `monthly_trends`, `category_analytics`, `overdue_analytics`): clear and reload on every run

---

## Analytics Features

| Feature | Endpoint | Chart |
|---------|----------|-------|
| Most Borrowed Books | `GET /api/analytics/most-borrowed` | Horizontal Bar Chart |
| Category-wise Borrowing | `GET /api/analytics/category-wise` | Donut Pie Chart + Table |
| Monthly Borrowing Trends | `GET /api/analytics/monthly-trends` | Line Chart (Borrows vs Returns) |
| Overdue Analysis | `GET /api/analytics/overdue` | Sortable Table |
| Dashboard Summary | `GET /api/analytics/dashboard` | Stat Cards |

---

## Setup & Running

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### Trigger ETL Manually

```bash
curl -X POST http://localhost:8000/api/etl/run
```

Or click **"Run ETL Pipeline"** on the Dashboard page.

---

## API Endpoints

### Books
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/books` | List all books (supports `?search=`) |
| POST | `/api/books` | Add a book |
| GET | `/api/books/{id}` | Get book by ID |
| PUT | `/api/books/{id}` | Update book |
| DELETE | `/api/books/{id}` | Delete book |

### Borrowers
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/borrowers` | List all borrowers (supports `?search=`) |
| POST | `/api/borrowers` | Add a borrower |
| PUT | `/api/borrowers/{id}` | Update borrower |
| DELETE | `/api/borrowers/{id}` | Delete borrower |

### Transactions
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/transactions` | List all (supports `?status=active\|returned\|overdue`) |
| POST | `/api/transactions` | Borrow a book |
| PUT | `/api/transactions/{id}/return` | Return a book |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/dashboard` | Summary statistics |
| GET | `/api/analytics/most-borrowed` | Top N most borrowed books |
| GET | `/api/analytics/category-wise` | Category breakdown |
| GET | `/api/analytics/monthly-trends` | Monthly trends (last N months) |
| GET | `/api/analytics/overdue` | Overdue transactions |

### ETL
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/etl/run` | Trigger full ETL pipeline |

---

## Dataset Summary

| File | Records | Key Fields |
|------|---------|------------|
| `books.csv` | 70 | book_id, title, author, category (10 categories), isbn, publication_year, total_copies, available_copies |
| `borrowers.csv` | 60 | borrower_id, name, email, phone, membership_date, membership_type (basic/premium/student) |
| `transactions.csv` | 220 | transaction_id, book_id, borrower_id, borrow_date, due_date, return_date, status, fine_amount |

Fine calculation: **₹0.50 per overdue day**

---

## Database Schema

```
books                    borrowers
──────────────────       ──────────────────
id (PK)                  id (PK)
title                    name
author                   email (unique)
category                 phone
isbn (unique)            membership_date
publication_year         membership_type
total_copies             address
available_copies
description

transactions             book_analytics
──────────────────       ──────────────────
id (PK)                  id (PK)
book_id (FK)             book_id
borrower_id (FK)         book_title
borrow_date              category
due_date                 total_borrows
return_date              avg_borrow_duration
status                   last_updated
fine_amount

monthly_trends           category_analytics       overdue_analytics
──────────────           ──────────────────       ──────────────────
id (PK)                  id (PK)                  id (PK)
year                     category (unique)        transaction_id
month                    total_borrows            book_title
total_borrows            unique_books             borrower_name
total_returns            unique_borrowers         due_date
overdue_count            last_updated             days_overdue
last_updated                                      fine_amount
                                                  last_updated
```

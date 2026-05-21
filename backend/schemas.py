from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ── Book schemas ──────────────────────────────────────────────────────────────


class BookBase(BaseModel):
    title: str
    author: str
    category: str
    isbn: str
    publication_year: Optional[int] = None
    total_copies: int = 1
    available_copies: int = 1
    description: Optional[str] = "No description available"


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    description: Optional[str] = None


class BookResponse(BookBase):
    id: int

    model_config = {"from_attributes": True}


# ── Borrower schemas ──────────────────────────────────────────────────────────


class BorrowerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    membership_date: Optional[datetime.date] = None
    membership_type: Optional[str] = "basic"
    address: Optional[str] = "Unknown"


class BorrowerCreate(BorrowerBase):
    pass


class BorrowerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    membership_date: Optional[datetime.date] = None
    membership_type: Optional[str] = None
    address: Optional[str] = None


class BorrowerResponse(BorrowerBase):
    id: int

    model_config = {"from_attributes": True}


# ── Transaction schemas ───────────────────────────────────────────────────────


class TransactionCreate(BaseModel):
    book_id: int
    borrower_id: int
    borrow_date: Optional[datetime.date] = None


class TransactionResponse(BaseModel):
    id: int
    book_id: int
    borrower_id: int
    borrow_date: datetime.date
    due_date: datetime.date
    return_date: Optional[datetime.date] = None
    status: str
    fine_amount: float
    # Denormalised fields for convenience
    book_title: Optional[str] = None
    borrower_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Analytics schemas ─────────────────────────────────────────────────────────


class DashboardStats(BaseModel):
    total_books: int
    total_borrowers: int
    total_transactions: int
    active_borrows: int
    overdue_count: int
    total_fine_collected: float


class MostBorrowedBook(BaseModel):
    book_id: int
    book_title: str
    category: str
    total_borrows: int
    avg_borrow_duration: float

    model_config = {"from_attributes": True}


class CategoryWise(BaseModel):
    category: str
    total_borrows: int
    unique_books: int
    unique_borrowers: int

    model_config = {"from_attributes": True}


class MonthlyTrendSchema(BaseModel):
    year: int
    month: int
    month_label: str
    total_borrows: int
    total_returns: int
    overdue_count: int

    model_config = {"from_attributes": True}


class OverdueItem(BaseModel):
    transaction_id: int
    book_title: str
    borrower_name: str
    due_date: datetime.date
    days_overdue: int
    fine_amount: float

    model_config = {"from_attributes": True}

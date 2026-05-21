from __future__ import annotations

import datetime

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False, index=True)
    publication_year = Column(Integer, nullable=True)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    description = Column(Text, default="No description available")

    transactions = relationship("Transaction", back_populates="book")


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    membership_date = Column(Date, default=datetime.date.today)
    membership_type = Column(String(20), default="basic")  # basic / premium / student
    address = Column(String(500), default="Unknown")

    transactions = relationship("Transaction", back_populates="borrower")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    status = Column(String(20), default="active")  # active / returned / overdue
    fine_amount = Column(Float, default=0.0)

    book = relationship("Book", back_populates="transactions")
    borrower = relationship("Borrower", back_populates="transactions")


# ── Analytics tables (populated by ETL) ──────────────────────────────────────


class BookAnalytics(Base):
    __tablename__ = "book_analytics"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    total_borrows = Column(Integer, default=0)
    avg_borrow_duration = Column(Float, default=0.0)
    last_updated = Column(Date, default=datetime.date.today)


class MonthlyTrend(Base):
    __tablename__ = "monthly_trends"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_borrows = Column(Integer, default=0)
    total_returns = Column(Integer, default=0)
    overdue_count = Column(Integer, default=0)
    last_updated = Column(Date, default=datetime.date.today)


class CategoryAnalytics(Base):
    __tablename__ = "category_analytics"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, unique=True)
    total_borrows = Column(Integer, default=0)
    unique_books = Column(Integer, default=0)
    unique_borrowers = Column(Integer, default=0)
    last_updated = Column(Date, default=datetime.date.today)


class OverdueAnalytics(Base):
    __tablename__ = "overdue_analytics"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False, unique=True)
    book_title = Column(String(255), nullable=False)
    borrower_name = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False)
    days_overdue = Column(Integer, default=0)
    fine_amount = Column(Float, default=0.0)
    last_updated = Column(Date, default=datetime.date.today)

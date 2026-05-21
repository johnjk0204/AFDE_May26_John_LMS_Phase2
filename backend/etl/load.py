from __future__ import annotations

import datetime
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from models import (
    Book,
    BookAnalytics,
    Borrower,
    CategoryAnalytics,
    MonthlyTrend,
    OverdueAnalytics,
    Transaction,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _safe_date(val) -> Optional[datetime.date]:
    """Convert a pandas Timestamp / NaT / string / date to a Python date or None."""
    if val is None:
        return None
    # Reject numpy arrays and other iterables that are not scalars
    if hasattr(val, "__len__") and not isinstance(val, str):
        return None
    # Check for NaT / NaN FIRST — before isinstance(datetime) checks because
    # pandas NaT is a subclass of datetime.datetime and would otherwise bypass this.
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    try:
        ts = pd.Timestamp(val)
        if pd.isna(ts):
            return None
        return ts.date()
    except Exception:
        return None


def _safe_float(val, default: float = 0.0) -> float:
    try:
        f = float(val)
        return f if pd.notna(f) else default
    except (TypeError, ValueError):
        return default


def _safe_int(val, default: int = 0) -> int:
    try:
        i = int(val)
        return i
    except (TypeError, ValueError):
        return default


# ── core loaders ──────────────────────────────────────────────────────────────


def load_books(df: pd.DataFrame, session: Session) -> None:
    """Upsert books by ISBN."""
    for _, row in df.iterrows():
        isbn = str(row.get("isbn", "")).strip()
        if not isbn:
            continue

        book = session.query(Book).filter(Book.isbn == isbn).first()
        if book is None:
            book = Book(isbn=isbn)
            session.add(book)

        book.title = str(row.get("title", "Unknown"))
        book.author = str(row.get("author", "Unknown"))
        book.category = str(row.get("category", "Unknown"))
        book.publication_year = _safe_int(row.get("publication_year"), 0) or None
        book.total_copies = _safe_int(row.get("total_copies"), 1)
        book.available_copies = _safe_int(row.get("available_copies"), 1)
        book.description = str(row.get("description", "No description available"))

        # Override id if provided so FK references from transactions work
        raw_id = row.get("id")
        if raw_id is not None and not (isinstance(raw_id, float) and pd.isna(raw_id)):
            book.id = _safe_int(raw_id)

    session.commit()


def load_borrowers(df: pd.DataFrame, session: Session) -> None:
    """Upsert borrowers by email."""
    for _, row in df.iterrows():
        email = str(row.get("email", "")).strip().lower()
        if not email:
            continue

        borrower = session.query(Borrower).filter(Borrower.email == email).first()
        if borrower is None:
            borrower = Borrower(email=email)
            session.add(borrower)

        borrower.name = str(row.get("name", "Unknown"))
        borrower.phone = str(row.get("phone", "")) or None
        borrower.membership_date = _safe_date(row.get("membership_date")) or datetime.date.today()
        borrower.membership_type = str(row.get("membership_type", "basic"))
        borrower.address = str(row.get("address", "Unknown"))

        raw_id = row.get("id")
        if raw_id is not None and not (isinstance(raw_id, float) and pd.isna(raw_id)):
            borrower.id = _safe_int(raw_id)

    session.commit()


def load_transactions(df: pd.DataFrame, session: Session) -> None:
    """Upsert transactions by id (CSV transaction_id → model id)."""
    for _, row in df.iterrows():
        txn_id = row.get("id")
        if txn_id is None or (isinstance(txn_id, float) and pd.isna(txn_id)):
            continue
        txn_id = int(txn_id)

        txn = session.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn is None:
            txn = Transaction(id=txn_id)
            session.add(txn)

        txn.book_id = _safe_int(row.get("book_id"))
        txn.borrower_id = _safe_int(row.get("borrower_id"))
        txn.borrow_date = _safe_date(row.get("borrow_date")) or datetime.date.today()
        txn.due_date = _safe_date(row.get("due_date")) or (
            txn.borrow_date + datetime.timedelta(days=14)
        )
        # Convert pandas NaT explicitly to Python None before assigning
        ret_val = row.get("return_date")
        txn.return_date = _safe_date(ret_val)
        txn.status = str(row.get("status", "active"))
        txn.fine_amount = _safe_float(row.get("fine_amount"), 0.0)

    session.commit()


# ── analytics loaders ─────────────────────────────────────────────────────────


def load_analytics(
    book_analytics: pd.DataFrame,
    monthly_trends: pd.DataFrame,
    category_analytics: pd.DataFrame,
    overdue_analytics: pd.DataFrame,
    session: Session,
) -> None:
    """Clear and reload all four analytics tables."""
    today = datetime.date.today()

    # ---- BookAnalytics -------------------------------------------------------
    session.query(BookAnalytics).delete()
    for _, row in book_analytics.iterrows():
        session.add(
            BookAnalytics(
                book_id=_safe_int(row.get("book_id")),
                book_title=str(row.get("book_title", "Unknown")),
                category=str(row.get("category", "Unknown")),
                total_borrows=_safe_int(row.get("total_borrows")),
                avg_borrow_duration=_safe_float(row.get("avg_borrow_duration")),
                last_updated=today,
            )
        )

    # ---- MonthlyTrend --------------------------------------------------------
    session.query(MonthlyTrend).delete()
    for _, row in monthly_trends.iterrows():
        session.add(
            MonthlyTrend(
                year=_safe_int(row.get("year")),
                month=_safe_int(row.get("month")),
                total_borrows=_safe_int(row.get("total_borrows")),
                total_returns=_safe_int(row.get("total_returns")),
                overdue_count=_safe_int(row.get("overdue_count")),
                last_updated=today,
            )
        )

    # ---- CategoryAnalytics ---------------------------------------------------
    session.query(CategoryAnalytics).delete()
    for _, row in category_analytics.iterrows():
        session.add(
            CategoryAnalytics(
                category=str(row.get("category", "Unknown")),
                total_borrows=_safe_int(row.get("total_borrows")),
                unique_books=_safe_int(row.get("unique_books")),
                unique_borrowers=_safe_int(row.get("unique_borrowers")),
                last_updated=today,
            )
        )

    # ---- OverdueAnalytics ----------------------------------------------------
    session.query(OverdueAnalytics).delete()
    for _, row in overdue_analytics.iterrows():
        due = _safe_date(row.get("due_date"))
        if due is None:
            continue
        session.add(
            OverdueAnalytics(
                transaction_id=_safe_int(row.get("transaction_id")),
                book_title=str(row.get("book_title", "Unknown")),
                borrower_name=str(row.get("borrower_name", "Unknown")),
                due_date=due,
                days_overdue=_safe_int(row.get("days_overdue")),
                fine_amount=_safe_float(row.get("fine_amount")),
                last_updated=today,
            )
        )

    session.commit()

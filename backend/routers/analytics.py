from __future__ import annotations

import calendar
import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Book,
    BookAnalytics,
    Borrower,
    CategoryAnalytics,
    MonthlyTrend,
    OverdueAnalytics,
    Transaction,
)
from schemas import (
    CategoryWise,
    DashboardStats,
    MonthlyTrendSchema,
    MostBorrowedBook,
    OverdueItem,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ── helpers ───────────────────────────────────────────────────────────────────


def _month_label(year: int, month: int) -> str:
    return f"{calendar.month_abbr[month]} {year}"


# ── endpoints ─────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    total_books = db.query(Book).count()
    total_borrowers = db.query(Borrower).count()
    total_transactions = db.query(Transaction).count()
    active_borrows = db.query(Transaction).filter(Transaction.status == "active").count()

    # Update overdue status on-the-fly before counting
    today = datetime.date.today()
    db.query(Transaction).filter(
        Transaction.status == "active",
        Transaction.due_date < today,
    ).update({"status": "overdue"}, synchronize_session=False)
    db.commit()

    overdue_count = db.query(Transaction).filter(Transaction.status == "overdue").count()
    total_fine = (
        db.query(func.sum(Transaction.fine_amount))
        .filter(Transaction.status == "returned")
        .scalar()
        or 0.0
    )

    return DashboardStats(
        total_books=total_books,
        total_borrowers=total_borrowers,
        total_transactions=total_transactions,
        active_borrows=active_borrows,
        overdue_count=overdue_count,
        total_fine_collected=round(float(total_fine), 2),
    )


@router.get("/most-borrowed", response_model=List[MostBorrowedBook])
def most_borrowed(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = db.query(BookAnalytics).order_by(BookAnalytics.total_borrows.desc()).limit(limit).all()

    if rows:
        return [
            MostBorrowedBook(
                book_id=r.book_id,
                book_title=r.book_title,
                category=r.category,
                total_borrows=r.total_borrows,
                avg_borrow_duration=r.avg_borrow_duration,
            )
            for r in rows
        ]

    # Fallback: compute on-the-fly
    results = (
        db.query(
            Book.id.label("book_id"),
            Book.title.label("book_title"),
            Book.category.label("category"),
            func.count(Transaction.id).label("total_borrows"),
        )
        .join(Transaction, Transaction.book_id == Book.id)
        .group_by(Book.id)
        .order_by(func.count(Transaction.id).desc())
        .limit(limit)
        .all()
    )
    return [
        MostBorrowedBook(
            book_id=r.book_id,
            book_title=r.book_title,
            category=r.category,
            total_borrows=r.total_borrows,
            avg_borrow_duration=0.0,
        )
        for r in results
    ]


@router.get("/category-wise", response_model=List[CategoryWise])
def category_wise(db: Session = Depends(get_db)):
    rows = db.query(CategoryAnalytics).order_by(CategoryAnalytics.total_borrows.desc()).all()

    if rows:
        return [
            CategoryWise(
                category=r.category,
                total_borrows=r.total_borrows,
                unique_books=r.unique_books,
                unique_borrowers=r.unique_borrowers,
            )
            for r in rows
        ]

    # Fallback: compute on-the-fly
    results = (
        db.query(
            Book.category.label("category"),
            func.count(Transaction.id).label("total_borrows"),
            func.count(func.distinct(Book.id)).label("unique_books"),
            func.count(func.distinct(Transaction.borrower_id)).label("unique_borrowers"),
        )
        .join(Transaction, Transaction.book_id == Book.id)
        .group_by(Book.category)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    return [
        CategoryWise(
            category=r.category,
            total_borrows=r.total_borrows,
            unique_books=r.unique_books,
            unique_borrowers=r.unique_borrowers,
        )
        for r in results
    ]


@router.get("/monthly-trends", response_model=List[MonthlyTrendSchema])
def monthly_trends(
    months: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MonthlyTrend)
        .order_by(MonthlyTrend.year.desc(), MonthlyTrend.month.desc())
        .limit(months)
        .all()
    )

    if rows:
        return [
            MonthlyTrendSchema(
                year=r.year,
                month=r.month,
                month_label=_month_label(r.year, r.month),
                total_borrows=r.total_borrows,
                total_returns=r.total_returns,
                overdue_count=r.overdue_count,
            )
            for r in reversed(rows)
        ]

    # Fallback: compute on-the-fly by iterating transactions in Python
    all_txns = db.query(Transaction).all()
    trend_map: dict = {}
    for txn in all_txns:
        if txn.borrow_date is None:
            continue
        key = (txn.borrow_date.year, txn.borrow_date.month)
        if key not in trend_map:
            trend_map[key] = {"total_borrows": 0, "total_returns": 0, "overdue_count": 0}
        trend_map[key]["total_borrows"] += 1
        if txn.return_date:
            trend_map[key]["total_returns"] += 1
        if txn.status == "overdue":
            trend_map[key]["overdue_count"] += 1

    sorted_keys = sorted(trend_map.keys())[-months:]
    return [
        MonthlyTrendSchema(
            year=k[0],
            month=k[1],
            month_label=_month_label(k[0], k[1]),
            total_borrows=trend_map[k]["total_borrows"],
            total_returns=trend_map[k]["total_returns"],
            overdue_count=trend_map[k]["overdue_count"],
        )
        for k in sorted_keys
    ]


@router.get("/overdue", response_model=List[OverdueItem])
def overdue_list(db: Session = Depends(get_db)):
    rows = db.query(OverdueAnalytics).order_by(OverdueAnalytics.days_overdue.desc()).all()

    if rows:
        return [
            OverdueItem(
                transaction_id=r.transaction_id,
                book_title=r.book_title,
                borrower_name=r.borrower_name,
                due_date=r.due_date,
                days_overdue=r.days_overdue,
                fine_amount=r.fine_amount,
            )
            for r in rows
        ]

    # Fallback: compute on-the-fly
    today = datetime.date.today()
    txns = (
        db.query(Transaction)
        .filter(Transaction.status == "overdue")
        .all()
    )
    result = []
    for txn in txns:
        days_overdue = (today - txn.due_date).days if txn.due_date else 0
        result.append(
            OverdueItem(
                transaction_id=txn.id,
                book_title=txn.book.title if txn.book else "Unknown",
                borrower_name=txn.borrower.name if txn.borrower else "Unknown",
                due_date=txn.due_date,
                days_overdue=max(days_overdue, 0),
                fine_amount=txn.fine_amount,
            )
        )
    return sorted(result, key=lambda x: x.days_overdue, reverse=True)

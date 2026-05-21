from __future__ import annotations

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Book, Borrower, Transaction
from schemas import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

_BORROW_DAYS = 14
_FINE_PER_DAY = 0.50


def _enrich(txn: Transaction) -> TransactionResponse:
    """Map ORM Transaction to the response schema, adding denormalised fields."""
    return TransactionResponse(
        id=txn.id,
        book_id=txn.book_id,
        borrower_id=txn.borrower_id,
        borrow_date=txn.borrow_date,
        due_date=txn.due_date,
        return_date=txn.return_date,
        status=txn.status,
        fine_amount=txn.fine_amount,
        book_title=txn.book.title if txn.book else None,
        borrower_name=txn.borrower.name if txn.borrower else None,
    )


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    status: Optional[str] = Query(None, description="Filter by status: active, returned, overdue"),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if status:
        query = query.filter(Transaction.status == status)
    txns = query.all()
    return [_enrich(t) for t in txns]


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    # Validate book exists and has copies available
    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="No copies of this book are currently available.")

    # Validate borrower exists
    borrower = db.query(Borrower).filter(Borrower.id == payload.borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found.")

    borrow_date = payload.borrow_date or datetime.date.today()
    due_date = borrow_date + datetime.timedelta(days=_BORROW_DAYS)

    txn = Transaction(
        book_id=payload.book_id,
        borrower_id=payload.borrower_id,
        borrow_date=borrow_date,
        due_date=due_date,
        return_date=None,
        status="active",
        fine_amount=0.0,
    )
    book.available_copies -= 1
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return _enrich(txn)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return _enrich(txn)


@router.put("/{transaction_id}/return", response_model=TransactionResponse)
def return_book(transaction_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if txn.status == "returned":
        raise HTTPException(status_code=400, detail="This book has already been returned.")

    return_date = datetime.date.today()
    txn.return_date = return_date
    txn.status = "returned"

    # Calculate fine if returned late
    if return_date > txn.due_date:
        days_late = (return_date - txn.due_date).days
        txn.fine_amount = round(days_late * _FINE_PER_DAY, 2)
    else:
        txn.fine_amount = 0.0

    # Restore available copy count
    book = db.query(Book).filter(Book.id == txn.book_id).first()
    if book:
        book.available_copies += 1

    db.commit()
    db.refresh(txn)
    return _enrich(txn)

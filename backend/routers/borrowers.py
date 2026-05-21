from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Borrower
from schemas import BorrowerCreate, BorrowerResponse, BorrowerUpdate

router = APIRouter(prefix="/api/borrowers", tags=["borrowers"])


@router.get("", response_model=List[BorrowerResponse])
def list_borrowers(
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db),
):
    query = db.query(Borrower)
    if search:
        like = f"%{search}%"
        query = query.filter(
            Borrower.name.ilike(like) | Borrower.email.ilike(like)
        )
    return query.all()


@router.post("", response_model=BorrowerResponse, status_code=201)
def create_borrower(payload: BorrowerCreate, db: Session = Depends(get_db)):
    existing = db.query(Borrower).filter(Borrower.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A borrower with this email already exists.")
    borrower = Borrower(**payload.model_dump())
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


@router.get("/{borrower_id}", response_model=BorrowerResponse)
def get_borrower(borrower_id: int, db: Session = Depends(get_db)):
    borrower = db.query(Borrower).filter(Borrower.id == borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found.")
    return borrower


@router.put("/{borrower_id}", response_model=BorrowerResponse)
def update_borrower(borrower_id: int, payload: BorrowerUpdate, db: Session = Depends(get_db)):
    borrower = db.query(Borrower).filter(Borrower.id == borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found.")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(borrower, field, value)
    db.commit()
    db.refresh(borrower)
    return borrower


@router.delete("/{borrower_id}", status_code=204)
def delete_borrower(borrower_id: int, db: Session = Depends(get_db)):
    borrower = db.query(Borrower).filter(Borrower.id == borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found.")
    db.delete(borrower)
    db.commit()

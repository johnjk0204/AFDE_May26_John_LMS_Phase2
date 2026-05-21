from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Book
from schemas import BookCreate, BookResponse, BookUpdate

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", response_model=List[BookResponse])
def list_books(
    search: Optional[str] = Query(None, description="Search by title, author, or category"),
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if search:
        like = f"%{search}%"
        query = query.filter(
            Book.title.ilike(like)
            | Book.author.ilike(like)
            | Book.category.ilike(like)
        )
    return query.all()


@router.post("", response_model=BookResponse, status_code=201)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    existing = db.query(Book).filter(Book.isbn == payload.isbn).first()
    if existing:
        raise HTTPException(status_code=400, detail="A book with this ISBN already exists.")
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    db.delete(book)
    db.commit()

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from sqlalchemy.orm import Session

from etl.extract import extract_books, extract_borrowers, extract_transactions
from etl.load import load_analytics, load_books, load_borrowers, load_transactions
from etl.transform import (
    compute_book_analytics,
    compute_category_analytics,
    compute_monthly_trends,
    compute_overdue_analytics,
    transform_books,
    transform_borrowers,
    transform_transactions,
)

logger = logging.getLogger(__name__)

# Resolve datasets directory relative to this file:
# etl/pipeline.py  →  backend/etl/  →  backend/  →  library-management-system/  →  datasets/
DATASETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "datasets")
)


def run_pipeline(session: Session) -> Dict[str, Any]:
    """Execute the full ETL pipeline and return a summary dict."""
    logger.info("ETL pipeline starting. Datasets directory: %s", DATASETS_DIR)

    # ── 1. Extract ────────────────────────────────────────────────────────────
    books_raw = extract_books(os.path.join(DATASETS_DIR, "books.csv"))
    borrowers_raw = extract_borrowers(os.path.join(DATASETS_DIR, "borrowers.csv"))
    transactions_raw = extract_transactions(os.path.join(DATASETS_DIR, "transactions.csv"))

    logger.info(
        "Extracted: %d books, %d borrowers, %d transactions",
        len(books_raw),
        len(borrowers_raw),
        len(transactions_raw),
    )

    # ── 2. Transform ──────────────────────────────────────────────────────────
    books_clean = transform_books(books_raw)
    borrowers_clean = transform_borrowers(borrowers_raw)
    transactions_clean = transform_transactions(transactions_raw)

    book_analytics = compute_book_analytics(transactions_clean, books_clean)
    monthly_trends = compute_monthly_trends(transactions_clean)
    category_analytics = compute_category_analytics(transactions_clean, books_clean)
    overdue_analytics = compute_overdue_analytics(
        transactions_clean, books_clean, borrowers_clean
    )

    logger.info(
        "Transformed: %d books, %d borrowers, %d transactions",
        len(books_clean),
        len(borrowers_clean),
        len(transactions_clean),
    )

    # ── 3. Load ───────────────────────────────────────────────────────────────
    load_books(books_clean, session)
    load_borrowers(borrowers_clean, session)
    load_transactions(transactions_clean, session)
    load_analytics(book_analytics, monthly_trends, category_analytics, overdue_analytics, session)

    logger.info("ETL pipeline completed successfully.")

    return {
        "status": "success",
        "books_loaded": len(books_clean),
        "borrowers_loaded": len(borrowers_clean),
        "transactions_loaded": len(transactions_clean),
        "analytics_generated": True,
        "book_analytics_rows": len(book_analytics),
        "monthly_trend_rows": len(monthly_trends),
        "category_analytics_rows": len(category_analytics),
        "overdue_analytics_rows": len(overdue_analytics),
    }

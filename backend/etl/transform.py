from __future__ import annotations

import datetime
import re

import pandas as pd


# ── Book transform ────────────────────────────────────────────────────────────


def transform_books(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate the books DataFrame."""
    df = df.copy()

    # Rename id column if it comes from CSV as 'book_id'
    if "book_id" in df.columns and "id" not in df.columns:
        df = df.rename(columns={"book_id": "id"})

    # Drop rows without an isbn
    df = df.dropna(subset=["isbn"])
    df["isbn"] = df["isbn"].astype(str).str.strip()
    df = df.drop_duplicates(subset=["isbn"], keep="first")

    # Fill missing description
    if "description" not in df.columns:
        df["description"] = "No description available"
    else:
        df["description"] = df["description"].fillna("No description available")

    # Coerce numeric columns
    for col in ["id", "publication_year", "total_copies", "available_copies"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Default copy counts to 1 if missing
    df["total_copies"] = df["total_copies"].fillna(1).astype(int)
    df["available_copies"] = df["available_copies"].fillna(1).astype(int)

    # Validate: available_copies must not exceed total_copies
    mask = df["available_copies"] > df["total_copies"]
    df.loc[mask, "available_copies"] = df.loc[mask, "total_copies"]

    df = df.reset_index(drop=True)
    return df


# ── Borrower transform ────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def transform_borrowers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate the borrowers DataFrame."""
    df = df.copy()

    # Rename id column
    if "borrower_id" in df.columns and "id" not in df.columns:
        df = df.rename(columns={"borrower_id": "id"})

    # Drop rows without an email
    df = df.dropna(subset=["email"])
    df["email"] = df["email"].astype(str).str.strip().str.lower()

    # Validate email format — remove rows with obviously bad emails
    valid_email_mask = df["email"].apply(lambda e: bool(_EMAIL_RE.match(e)))
    df = df[valid_email_mask]

    # Drop duplicate emails
    df = df.drop_duplicates(subset=["email"], keep="first")

    # Fill missing address
    if "address" not in df.columns:
        df["address"] = "Unknown"
    else:
        df["address"] = df["address"].fillna("Unknown")

    # membership_type default
    if "membership_type" not in df.columns:
        df["membership_type"] = "basic"
    else:
        df["membership_type"] = df["membership_type"].fillna("basic")

    # Parse membership_date to datetime
    if "membership_date" in df.columns:
        df["membership_date"] = pd.to_datetime(df["membership_date"], errors="coerce")

    # Coerce id
    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce")

    df = df.reset_index(drop=True)
    return df


# ── Transaction transform ─────────────────────────────────────────────────────


def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean, parse dates, recompute status and fine for the transactions DataFrame."""
    df = df.copy()

    # Rename id column
    if "transaction_id" in df.columns and "id" not in df.columns:
        df = df.rename(columns={"transaction_id": "id"})

    # Drop duplicate transaction ids
    df = df.dropna(subset=["id"])
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)
    df = df.drop_duplicates(subset=["id"], keep="first")

    # Coerce FK columns
    for col in ["book_id", "borrower_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse date columns
    for col in ["borrow_date", "due_date", "return_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Ensure return_date NaT for missing values
    df["return_date"] = df["return_date"].where(df["return_date"].notna(), other=pd.NaT)

    today = pd.Timestamp(datetime.date.today())

    def _compute_status(row: pd.Series) -> str:
        if pd.notna(row["return_date"]):
            return "returned"
        if pd.notna(row["due_date"]) and row["due_date"] < today:
            return "overdue"
        return "active"

    df["status"] = df.apply(_compute_status, axis=1)

    def _compute_fine(row: pd.Series) -> float:
        if row["status"] == "returned":
            # Fine if returned late
            if pd.notna(row["return_date"]) and pd.notna(row["due_date"]):
                if row["return_date"] > row["due_date"]:
                    days_late = (row["return_date"] - row["due_date"]).days
                    return round(days_late * 0.50, 2)
            return 0.0
        if row["status"] == "overdue":
            if pd.notna(row["due_date"]):
                days_overdue = (today - row["due_date"]).days
                return round(max(days_overdue, 0) * 0.50, 2)
        return 0.0

    df["fine_amount"] = df.apply(_compute_fine, axis=1)

    df = df.reset_index(drop=True)
    return df


# ── Analytics computations ────────────────────────────────────────────────────


def compute_book_analytics(
    transactions_df: pd.DataFrame,
    books_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-book borrow counts and average borrow durations."""
    txn = transactions_df.copy()
    books = books_df.copy()

    if txn.empty or books.empty:
        return pd.DataFrame(
            columns=["book_id", "book_title", "category", "total_borrows", "avg_borrow_duration"]
        )

    # Compute borrow duration (days) for returned transactions
    # Use float column (not datetime) to avoid dtype conflicts with NaT
    txn["borrow_duration"] = float("nan")
    returned_mask = txn["return_date"].notna() & txn["borrow_date"].notna()
    duration_series = (
        txn.loc[returned_mask, "return_date"] - txn.loc[returned_mask, "borrow_date"]
    ).dt.days.astype(float)
    txn.loc[returned_mask, "borrow_duration"] = duration_series.values

    grouped = (
        txn.groupby("book_id")
        .agg(
            total_borrows=("id", "count"),
            avg_borrow_duration=("borrow_duration", "mean"),
        )
        .reset_index()
    )
    grouped["avg_borrow_duration"] = grouped["avg_borrow_duration"].fillna(0.0).round(2)

    # Join with books to get title and category
    book_id_col = "id" if "id" in books.columns else "book_id"
    books_slim = books[[book_id_col, "title", "category"]].rename(
        columns={book_id_col: "book_id", "title": "book_title"}
    )
    books_slim["book_id"] = pd.to_numeric(books_slim["book_id"], errors="coerce")
    grouped["book_id"] = pd.to_numeric(grouped["book_id"], errors="coerce")

    result = grouped.merge(books_slim, on="book_id", how="left")
    result["book_title"] = result["book_title"].fillna("Unknown")
    result["category"] = result["category"].fillna("Unknown")

    return result[["book_id", "book_title", "category", "total_borrows", "avg_borrow_duration"]]


def compute_monthly_trends(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly borrow / return / overdue counts."""
    txn = transactions_df.copy()

    if txn.empty:
        return pd.DataFrame(
            columns=["year", "month", "total_borrows", "total_returns", "overdue_count"]
        )

    txn["borrow_date"] = pd.to_datetime(txn["borrow_date"], errors="coerce")
    txn = txn.dropna(subset=["borrow_date"])
    txn["year"] = txn["borrow_date"].dt.year
    txn["month"] = txn["borrow_date"].dt.month

    borrows = (
        txn.groupby(["year", "month"]).size().reset_index(name="total_borrows")
    )
    returns = (
        txn[txn["status"] == "returned"]
        .groupby(["year", "month"])
        .size()
        .reset_index(name="total_returns")
    )
    overdues = (
        txn[txn["status"] == "overdue"]
        .groupby(["year", "month"])
        .size()
        .reset_index(name="overdue_count")
    )

    result = borrows.merge(returns, on=["year", "month"], how="left")
    result = result.merge(overdues, on=["year", "month"], how="left")
    result["total_returns"] = result["total_returns"].fillna(0).astype(int)
    result["overdue_count"] = result["overdue_count"].fillna(0).astype(int)

    return result.sort_values(["year", "month"]).reset_index(drop=True)


def compute_category_analytics(
    transactions_df: pd.DataFrame,
    books_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-category borrow stats."""
    txn = transactions_df.copy()
    books = books_df.copy()

    if txn.empty or books.empty:
        return pd.DataFrame(
            columns=["category", "total_borrows", "unique_books", "unique_borrowers"]
        )

    book_id_col = "id" if "id" in books.columns else "book_id"
    books_slim = books[[book_id_col, "category"]].rename(columns={book_id_col: "book_id"})
    books_slim["book_id"] = pd.to_numeric(books_slim["book_id"], errors="coerce")
    txn["book_id"] = pd.to_numeric(txn["book_id"], errors="coerce")

    merged = txn.merge(books_slim, on="book_id", how="left")
    merged["category"] = merged["category"].fillna("Unknown")

    result = (
        merged.groupby("category")
        .agg(
            total_borrows=("id", "count"),
            unique_books=("book_id", "nunique"),
            unique_borrowers=("borrower_id", "nunique"),
        )
        .reset_index()
    )
    return result.sort_values("total_borrows", ascending=False).reset_index(drop=True)


def compute_overdue_analytics(
    transactions_df: pd.DataFrame,
    books_df: pd.DataFrame,
    borrowers_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build overdue analytics by joining overdue transactions with books and borrowers."""
    txn = transactions_df.copy()
    books = books_df.copy()
    borrowers = borrowers_df.copy()

    overdue = txn[txn["status"] == "overdue"].copy()
    if overdue.empty:
        return pd.DataFrame(
            columns=[
                "transaction_id",
                "book_title",
                "borrower_name",
                "due_date",
                "days_overdue",
                "fine_amount",
            ]
        )

    # Prepare book lookup
    book_id_col = "id" if "id" in books.columns else "book_id"
    books_slim = books[[book_id_col, "title"]].rename(
        columns={book_id_col: "book_id", "title": "book_title"}
    )
    books_slim["book_id"] = pd.to_numeric(books_slim["book_id"], errors="coerce")

    # Prepare borrower lookup
    borrower_id_col = "id" if "id" in borrowers.columns else "borrower_id"
    borrowers_slim = borrowers[[borrower_id_col, "name"]].rename(
        columns={borrower_id_col: "borrower_id", "name": "borrower_name"}
    )
    borrowers_slim["borrower_id"] = pd.to_numeric(borrowers_slim["borrower_id"], errors="coerce")

    overdue["book_id"] = pd.to_numeric(overdue["book_id"], errors="coerce")
    overdue["borrower_id"] = pd.to_numeric(overdue["borrower_id"], errors="coerce")

    merged = overdue.merge(books_slim, on="book_id", how="left")
    merged = merged.merge(borrowers_slim, on="borrower_id", how="left")
    merged["book_title"] = merged["book_title"].fillna("Unknown")
    merged["borrower_name"] = merged["borrower_name"].fillna("Unknown")

    today = pd.Timestamp(datetime.date.today())
    merged["due_date"] = pd.to_datetime(merged["due_date"], errors="coerce")
    merged["days_overdue"] = (today - merged["due_date"]).dt.days.clip(lower=0).fillna(0).astype(int)

    result = merged[
        ["id", "book_title", "borrower_name", "due_date", "days_overdue", "fine_amount"]
    ].rename(columns={"id": "transaction_id"})

    return result.sort_values("days_overdue", ascending=False).reset_index(drop=True)

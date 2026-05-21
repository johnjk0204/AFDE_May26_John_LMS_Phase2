from __future__ import annotations

import pandas as pd


def extract_books(csv_path: str) -> pd.DataFrame:
    """Read books CSV and return a DataFrame.

    Expected columns: book_id, title, author, category, isbn,
                      publication_year, total_copies, available_copies
    The optional 'description' column is kept if present.
    """
    df = pd.read_csv(csv_path, dtype=str)
    # Normalise column names to lower-case with underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def extract_borrowers(csv_path: str) -> pd.DataFrame:
    """Read borrowers CSV and return a DataFrame.

    Expected columns: borrower_id, name, email, phone,
                      membership_date, membership_type, address
    """
    df = pd.read_csv(csv_path, dtype=str)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def extract_transactions(csv_path: str) -> pd.DataFrame:
    """Read transactions CSV and return a DataFrame.

    Expected columns: transaction_id, book_id, borrower_id, borrow_date,
                      due_date, return_date, status, fine_amount
    """
    df = pd.read_csv(csv_path, dtype=str)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

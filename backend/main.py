from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, SessionLocal, engine, get_db
from routers import analytics, books, borrowers, transactions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Library Management System API",
    version="2.0.0",
    description="REST API for managing books, borrowers, transactions and ETL-powered analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup() -> None:
    """Auto-run ETL pipeline on startup when the analytics tables are empty."""
    from models import BookAnalytics  # local import to avoid circular reference at module level

    db = SessionLocal()
    try:
        count = db.query(BookAnalytics).count()
        if count == 0:
            logger.info("Analytics tables empty — running ETL pipeline on startup …")
            from etl.pipeline import run_pipeline

            result = run_pipeline(db)
            logger.info("Startup ETL result: %s", result)
        else:
            logger.info("Analytics tables already populated (%d rows) — skipping ETL.", count)
    except Exception as exc:  # noqa: BLE001
        logger.error("Startup ETL failed: %s", exc)
    finally:
        db.close()


# ── Root ──────────────────────────────────────────────────────────────────────


@app.get("/", tags=["root"])
def root():
    return {"message": "Library Management System API v2.0"}


# ── ETL trigger endpoint ──────────────────────────────────────────────────────


@app.post("/api/etl/run", tags=["etl"])
def trigger_etl(db=Depends(get_db)):
    """Manually trigger the ETL pipeline."""
    from etl.pipeline import run_pipeline

    return run_pipeline(db)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(books.router)
app.include_router(borrowers.router)
app.include_router(transactions.router)
app.include_router(analytics.router)

from dotenv import load_dotenv
load_dotenv()  # Load .env before any env-var reads (watsonx credentials, etc.)

import logging
import os
from urllib.parse import urlparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func as sa_func, select

from . import orm_models as dbm
from .dashboard import router as dashboard_router
from .data import POLES, SEGMENTS, get_summary
from .database import Base, SessionLocal, USING_DEFAULT_SQLITE, engine
from .models import CircuitSegment, PoleRiskProfile, RiskBand, Summary

app = FastAPI(title="Amped Up", version="0.2.0")


def _normalize_origin(origin: str) -> str | None:
    cleaned = origin.strip().rstrip("/")
    if not cleaned:
        return None
    if cleaned.startswith("https//"):
        cleaned = cleaned.replace("https//", "https://", 1)
    if cleaned.startswith("http//"):
        cleaned = cleaned.replace("http//", "http://", 1)

    parsed = urlparse(cleaned)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".lower()


def _allowed_origins() -> list[str]:
    default_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "https://amped-up.online",
        "https://www.amped-up.online",
        "https://carlsciz.github.io",
    ]
    configured = [
        normalized
        for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
        if (normalized := _normalize_origin(origin))
    ]
    return list(dict.fromkeys([*default_origins, *configured]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def initialize_dev_database() -> None:
    from sqlalchemy import text

    if USING_DEFAULT_SQLITE:
        Base.metadata.create_all(bind=engine)

    # Idempotent risk-column migration — runs on every backend engine (SQLite + Postgres).
    # Uses engine-agnostic type names: REAL/JSONB/TIMESTAMPTZ are handled below.
    is_postgres = not USING_DEFAULT_SQLITE
    risk_columns = [
        ("risk_score",        "DOUBLE PRECISION" if is_postgres else "REAL"),
        ("predicted_severity","VARCHAR(16)"       if is_postgres else "TEXT"),
        ("risk_factors",      "JSONB"             if is_postgres else "TEXT"),
        ("risk_computed_at",  "TIMESTAMPTZ"       if is_postgres else "TEXT"),
    ]
    with engine.connect() as conn:
        for col, col_type in risk_columns:
            try:
                conn.execute(text(f"ALTER TABLE poles ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()  # column already exists — safe to ignore

    if not USING_DEFAULT_SQLITE:
        return

    with SessionLocal() as db:
        user_count = db.scalar(select(sa_func.count()).select_from(dbm.User)) or 0
    if user_count:
        return

    from .seed_dashboard_data import seed_dashboard_data

    seed_dashboard_data()


@app.get("/api/summary", response_model=Summary)
def summary() -> Summary:
    return get_summary()


@app.get("/api/poles", response_model=list[PoleRiskProfile])
def poles(
    circuit: str | None = None,
    segment: str | None = None,
    min_score: float = Query(0, ge=0, le=100),
    band: RiskBand | None = None,
    driver: str | None = None,
) -> list[PoleRiskProfile]:
    results = POLES
    if circuit:
        results = [pole for pole in results if pole.circuit_id == circuit]
    if segment:
        results = [pole for pole in results if pole.segment_id == segment]
    if band:
        results = [pole for pole in results if pole.risk_band == band]
    if driver:
        results = [pole for pole in results if driver.lower() in pole.top_drivers]
    return sorted([pole for pole in results if pole.risk_score >= min_score], key=lambda p: p.priority_rank)


@app.get("/api/poles/{pole_id}", response_model=PoleRiskProfile)
def pole_detail(pole_id: str) -> PoleRiskProfile:
    for pole in POLES:
        if pole.id == pole_id:
            return pole
    raise HTTPException(status_code=404, detail="Pole not found")


@app.get("/api/circuits", response_model=list[CircuitSegment])
def circuits(
    circuit: str | None = None,
    min_score: float = Query(0, ge=0, le=100),
    band: RiskBand | None = None,
) -> list[CircuitSegment]:
    results = SEGMENTS
    if circuit:
        results = [segment for segment in results if segment.circuit_id == circuit]
    if band:
        results = [segment for segment in results if segment.risk_band == band]
    return [segment for segment in results if segment.risk_score >= min_score]

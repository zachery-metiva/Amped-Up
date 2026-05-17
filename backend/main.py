from dotenv import load_dotenv
load_dotenv()  # Load .env before any env-var reads (watsonx credentials, etc.)

import logging
import os
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func as sa_func, select

from . import orm_models as dbm
from .dashboard import router as dashboard_router
from .data import POLES, SEGMENTS, get_summary
from .database import Base, SessionLocal, USING_DEFAULT_SQLITE, engine
from .models import CircuitSegment, PoleRiskProfile, RiskBand, Summary
from .zeus_api import router as zeus_router

app = FastAPI(title="Amped Up", version="0.2.0")


def _allowed_origins() -> list[str]:
    local_origins = [
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
    ]
    configured = [
        origin.strip().rstrip("/")
        for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
        if origin.strip()
    ]
    return [*local_origins, *configured]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(zeus_router)


@app.on_event("startup")
def initialize_dev_database() -> None:
    if not USING_DEFAULT_SQLITE:
        return

    Base.metadata.create_all(bind=engine)
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

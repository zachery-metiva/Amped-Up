from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .dashboard import router as dashboard_router
from .data import POLES, SEGMENTS, get_summary
from .models import CircuitSegment, PoleRiskProfile, RiskBand, Summary

app = FastAPI(title="Amped Up", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    # Allow any Vite dev-server port (5173–5180) plus production origins.
    # Vite auto-increments the port when the default is busy.
    allow_origins=[
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)


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

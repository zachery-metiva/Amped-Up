"""
Optimized bulk risk scorer for the Detroit metro pole inventory.

Key shortcuts (safe for this geography):
  - Storm/wind score fetched ONCE for the Detroit centroid — all poles within
    ~50 km have the same historical weather record.
  - Terrain score is a constant 5.0 (Michigan is essentially flat; USGS would
    return ~0-2 m elevation delta over 50 m for every pole in the dataset).
  - Flood zone + vegetation are the real differentiators and are fetched per
    pole in parallel (ThreadPoolExecutor).

Usage:
    python seed_risk.py [--limit N] [--workers W]
    python seed_risk.py --limit 200 --workers 8
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from backend.database import SessionLocal
from backend import orm_models as dbm
from backend.data_fetchers import (
    fetch_flood_zone_score,
    fetch_storm_exposure_score,
    fetch_vegetation_score,
    derive_soil_score,
)

# Detroit geographic centroid
DETROIT_LAT = 42.3314
DETROIT_LON = -83.0458

WEIGHTS = {
    "vegetation": 0.30,
    "flood":      0.30,
    "storm":      0.15,
    "soil":       0.12,
    "age":        0.08,
    "terrain":    0.05,
}

TERRAIN_SCORE_MICHIGAN = 5.0   # flat; same for every Detroit-area pole
TERRAIN_SLOPE_PCT      = 0.25


def score_to_severity(s: float) -> str:
    if s >= 58: return "critical"
    if s >= 40: return "high"
    if s >= 22: return "medium"
    return "low"


def age_score(pole: dbm.Pole) -> float:
    if not pole.installed_at:
        return 40.0
    years = (datetime.now(timezone.utc) - pole.installed_at).days / 365.25
    return min(100.0, max(0.0, (years - 10.0) / 40.0 * 100.0))


def score_one(pole: dbm.Pole, shared_storm: float, storm_meta: dict) -> dict:
    """Score a single pole. Called from a thread."""
    lat, lon = pole.latitude, pole.longitude

    flood_score, flood_zone = fetch_flood_zone_score(lat, lon)
    veg_score               = fetch_vegetation_score(lat, lon)
    terrain_score           = TERRAIN_SCORE_MICHIGAN
    soil_score              = derive_soil_score(flood_zone, terrain_score)
    a_score                 = age_score(pole)

    composite = (
        veg_score     * WEIGHTS["vegetation"]
        + flood_score   * WEIGHTS["flood"]
        + shared_storm  * WEIGHTS["storm"]
        + soil_score    * WEIGHTS["soil"]
        + a_score       * WEIGHTS["age"]
        + terrain_score * WEIGHTS["terrain"]
    )
    composite = round(composite, 2)

    factors = {
        "vegetation": {"score": round(veg_score, 1),     "weight": WEIGHTS["vegetation"], "label": "Vegetation proximity"},
        "storm":      {"score": round(shared_storm, 1),  "weight": WEIGHTS["storm"],      "label": "Storm / wind exposure", **storm_meta},
        "flood":      {"score": round(flood_score, 1),   "weight": WEIGHTS["flood"],      "label": "Flood zone risk", "zone": flood_zone},
        "terrain":    {"score": round(terrain_score, 1), "weight": WEIGHTS["terrain"],    "label": "Terrain slope (MI flat)", "slope_pct": TERRAIN_SLOPE_PCT},
        "soil":       {"score": round(soil_score, 1),    "weight": WEIGHTS["soil"],       "label": "Soil drainage"},
        "age":        {"score": round(a_score, 1),       "weight": WEIGHTS["age"],        "label": "Estimated pole age"},
        "_composite": composite,
    }

    return {
        "pole_id":            pole.id,
        "risk_score":         composite,
        "predicted_severity": score_to_severity(composite),
        "risk_factors":       factors,
        "risk_computed_at":   datetime.now(timezone.utc),
    }


def run(limit: int = 200, workers: int = 6) -> None:
    # ── 1. Fetch storm score once for the whole metro ────────────────────────
    print("Fetching Detroit metro storm/wind baseline… ", end="", flush=True)
    shared_storm, storm_meta = fetch_storm_exposure_score(DETROIT_LAT, DETROIT_LON)
    print(f"{shared_storm:.1f} (max gust {storm_meta.get('max_gust_kmh')} km/h)")

    # ── 2. Load poles from DB ────────────────────────────────────────────────
    db = SessionLocal()
    poles = db.scalars(
        select(dbm.Pole)
        .where(dbm.Pole.risk_score.is_(None))   # skip already-scored
        .limit(limit)
    ).all()
    print(f"Scoring {len(poles)} unscored poles with {workers} workers…\n")

    # ── 3. Parallel fetch + score ────────────────────────────────────────────
    results: list[dict] = []
    errors  = 0
    start   = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(score_one, pole, shared_storm, storm_meta): pole
            for pole in poles
        }
        done = 0
        for fut in as_completed(futures):
            pole = futures[fut]
            done += 1
            try:
                result = fut.result()
                results.append(result)
                elapsed = time.time() - start
                rate    = done / elapsed
                eta     = (len(poles) - done) / rate if rate > 0 else 0
                print(
                    f"  [{done:>3}/{len(poles)}] {pole.id[:24]:<24} "
                    f"{result['risk_score']:>5.1f}  {result['predicted_severity']:<8} "
                    f"  ETA {eta:>4.0f}s",
                    flush=True,
                )
            except Exception as exc:
                errors += 1
                print(f"  [{done:>3}/{len(poles)}] {pole.id} ERROR: {exc}", file=sys.stderr)

    # ── 4. Write to DB ───────────────────────────────────────────────────────
    print(f"\nWriting {len(results)} results to database…")
    written = 0
    for r in results:
        try:
            pole = db.get(dbm.Pole, r["pole_id"])
            if pole:
                pole.risk_score         = r["risk_score"]
                pole.predicted_severity = r["predicted_severity"]
                pole.risk_factors       = r["risk_factors"]
                pole.risk_computed_at   = r["risk_computed_at"]
                db.commit()
                written += 1
        except Exception as exc:
            db.rollback()
            print(f"  DB write failed for {r['pole_id']}: {exc}", file=sys.stderr)

    db.close()

    elapsed = time.time() - start
    from collections import Counter
    dist = Counter(r["predicted_severity"] for r in results)
    print(f"\n✓  {written} poles scored in {elapsed:.0f}s  ({errors} errors)")
    print(f"   critical={dist['critical']}  high={dist['high']}  medium={dist['medium']}  low={dist['low']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int, default=200, help="Max poles to score (default 200)")
    parser.add_argument("--workers", type=int, default=6,   help="Parallel fetch threads (default 6)")
    args = parser.parse_args()
    run(limit=args.limit, workers=args.workers)

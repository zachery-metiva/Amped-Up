"""
Composite risk scoring engine for utility poles.

Weights (must sum to 1.0) — tuned for Detroit metro geography:
  vegetation  0.30  — canopy encroachment & line contact (highest local variation)
  flood       0.30  — waterway proximity → soil saturation, groundline decay
  storm       0.15  — metro-wide wind/ice baseline (low variation within service territory)
  soil        0.12  — drainage class (derived from flood zone label)
  age         0.08  — cumulative wear
  terrain     0.05  — slope (Michigan glacial plain; near-zero for all poles)

Severity thresholds — calibrated to actual score distribution for Detroit metro
(storm baseline ~48, vegetation 12-85, flood 12-90, terrain ~5):
  58-100  critical   — waterway-adjacent + high-canopy corridors
  40-57   high       — near waterways OR high urban forest cover
  22-39   medium     — suburban residential (most of the network)
  0-21    low        — dense downtown / industrial (low canopy, far from water)
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import orm_models as dbm
from .data_fetchers import (
    derive_soil_score,
    fetch_flood_zone_score,
    fetch_storm_exposure_score,
    fetch_terrain_score,
    fetch_vegetation_score,
)

WEIGHTS = {
    "vegetation": 0.30,
    "flood":      0.30,
    "storm":      0.15,
    "soil":       0.12,
    "age":        0.08,
    "terrain":    0.05,
}


def _age_score(pole: dbm.Pole) -> float:
    if not pole.installed_at:
        return 40.0  # unknown age → moderate assumed risk
    years = (datetime.now(timezone.utc) - pole.installed_at).days / 365.25
    # <10 yrs → ~0, 50 yrs → 100
    return min(100.0, max(0.0, (years - 10.0) / 40.0 * 100.0))


def _score_to_severity(score: float) -> str:
    if score >= 58:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 22:
        return "medium"
    return "low"


def compute_pole_risk(pole: dbm.Pole) -> dict:
    """
    Fetch all environmental signals and compute composite risk for one pole.
    Returns a dict ready to be merged into the Pole ORM row.
    """
    lat, lon = pole.latitude, pole.longitude

    veg_score = fetch_vegetation_score(lat, lon)
    storm_score, storm_meta = fetch_storm_exposure_score(lat, lon)
    flood_score, flood_zone = fetch_flood_zone_score(lat, lon)
    terrain_score, slope_pct = fetch_terrain_score(lat, lon)
    soil_score = derive_soil_score(flood_zone, terrain_score)
    age_score = _age_score(pole)

    composite = (
        veg_score   * WEIGHTS["vegetation"]
        + storm_score * WEIGHTS["storm"]
        + flood_score * WEIGHTS["flood"]
        + terrain_score * WEIGHTS["terrain"]
        + soil_score  * WEIGHTS["soil"]
        + age_score   * WEIGHTS["age"]
    )

    factors = {
        "vegetation": {"score": round(veg_score, 1),   "weight": WEIGHTS["vegetation"], "label": "Vegetation proximity"},
        "storm":      {"score": round(storm_score, 1),  "weight": WEIGHTS["storm"],      "label": "Storm / wind exposure", **storm_meta},
        "flood":      {"score": round(flood_score, 1),  "weight": WEIGHTS["flood"],      "label": "Flood zone risk", "zone": flood_zone},
        "terrain":    {"score": round(terrain_score, 1),"weight": WEIGHTS["terrain"],    "label": "Terrain slope", "slope_pct": slope_pct},
        "soil":       {"score": round(soil_score, 1),   "weight": WEIGHTS["soil"],       "label": "Soil drainage"},
        "age":        {"score": round(age_score, 1),    "weight": WEIGHTS["age"],        "label": "Estimated pole age"},
        "_composite": round(composite, 2),
    }

    return {
        "risk_score": round(composite, 2),
        "predicted_severity": _score_to_severity(composite),
        "risk_factors": factors,
        "risk_computed_at": datetime.now(timezone.utc),
    }

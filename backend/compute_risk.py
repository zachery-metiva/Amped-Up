"""
Usage:  python -m backend.compute_risk [--limit N] [--pole POLE_ID]

Iterates all Pole rows (or a subset), fetches public-data risk signals,
and writes risk_score / predicted_severity / risk_factors back to the DB.
"""
from __future__ import annotations

import argparse
import sys
import time

from sqlalchemy import select

from .database import SessionLocal
from . import orm_models as dbm
from .risk_engine import compute_pole_risk


def run(limit: int | None = None, pole_id: str | None = None) -> None:
    db = SessionLocal()
    try:
        q = select(dbm.Pole)
        if pole_id:
            q = q.where(dbm.Pole.id == pole_id)
        poles = db.scalars(q).all()
        if limit:
            poles = poles[:limit]

        total = len(poles)
        print(f"Computing risk for {total} pole(s)…")
        for i, pole in enumerate(poles, 1):
            try:
                updates = compute_pole_risk(pole)
                for k, v in updates.items():
                    setattr(pole, k, v)
                predicted = db.get(dbm.PredictedReport, f"PRED-{pole.id}")
                if not predicted:
                    predicted = dbm.PredictedReport(id=f"PRED-{pole.id}", pole_id=pole.id)
                    db.add(predicted)
                predicted.title = f"Predicted {updates['predicted_severity']} risk - {pole.id}"
                predicted.predicted_severity = dbm.Severity(updates["predicted_severity"])
                predicted.risk_score = updates["risk_score"]
                predicted.risk_factors = updates["risk_factors"]
                predicted.generated_at = updates["risk_computed_at"]
                if predicted.status != dbm.ReportStatus.DISMISSED:
                    predicted.status = dbm.ReportStatus.OPEN
                db.commit()
                sev = updates["predicted_severity"]
                score = updates["risk_score"]
                print(f"  [{i}/{total}] {pole.id}: {score:.1f} → {sev}")
            except Exception as exc:
                print(f"  [{i}/{total}] {pole.id}: ERROR — {exc}", file=sys.stderr)
                db.rollback()
            # Brief pause to be polite to public APIs
            time.sleep(0.4)
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pole", type=str, default=None)
    args = parser.parse_args()
    run(limit=args.limit, pole_id=args.pole)

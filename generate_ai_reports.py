"""
Retroactively generate AI risk-assessment reports for all scored poles.

Usage:
    python3 generate_ai_reports.py [--limit N] [--force]

Options:
    --limit N   Only process first N scored poles (default: all)
    --force     Regenerate even if an AI report already exists
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, func
from backend.database import SessionLocal
from backend import orm_models as dbm
from backend.ai_report_generator import upsert_ai_report, AI_REPORT_ID_PREFIX, ensure_ai_user


def run(limit: int | None = None, force: bool = False) -> None:
    db = SessionLocal()
    try:
        # Ensure the AI system user exists
        ensure_ai_user(db)
        db.commit()

        # Fetch all scored poles
        q = select(dbm.Pole).where(dbm.Pole.risk_score.isnot(None)).order_by(dbm.Pole.risk_score.desc())
        poles = db.scalars(q).all()
        if limit:
            poles = poles[:limit]

        total = len(poles)
        print(f"Generating AI reports for {total} scored pole(s)…")

        created = updated = skipped = errors = 0

        for i, pole in enumerate(poles, 1):
            try:
                db.expire_all()  # flush identity-map cache before each check
                report_id = f"{AI_REPORT_ID_PREFIX}{pole.id}"
                existing = db.scalar(select(dbm.Report).where(dbm.Report.id == report_id))

                if existing and not force:
                    skipped += 1
                    if i % 50 == 0:
                        print(f"  [{i}/{total}] … {skipped} skipped so far (use --force to regenerate)")
                    continue

                was_new = existing is None
                upsert_ai_report(db, pole)
                db.commit()

                if was_new:
                    created += 1
                else:
                    updated += 1

                if i % 50 == 0 or i == total:
                    print(f"  [{i}/{total}] {pole.id}: {pole.risk_score:.1f} → {pole.predicted_severity}")

            except Exception as exc:
                print(f"  [{i}/{total}] {pole.id}: ERROR — {exc}", file=sys.stderr)
                db.rollback()
                errors += 1

    finally:
        db.close()

    print()
    print(f"Done. Created: {created}  Updated: {updated}  Skipped: {skipped}  Errors: {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AI risk reports for scored poles.")
    parser.add_argument("--limit", type=int, default=None, help="Max poles to process")
    parser.add_argument("--force", action="store_true", help="Regenerate existing AI reports")
    args = parser.parse_args()
    run(limit=args.limit, force=args.force)

"""One-shot, paginated Asset Integrity Monitoring worker.

Run with ``python -m app.workers.integrity`` from the backend directory. A
single invocation scans the finite set of assets present at its start and exits.
Schedule invocations externally; this module does not start an API background loop.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
import logging
from typing import Callable
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.services.asset_integrity import verify_asset_integrity

logger = logging.getLogger(__name__)
SessionFactory = Callable[[], Session]


@dataclass(frozen=True)
class IntegrityScanSummary:
    scanned: int
    skipped: int
    failed: int
    status_counts: dict[str, int]
    last_asset_id: uuid.UUID | None


def run_integrity_scan(
    batch_size: int = 100,
    session_factory: SessionFactory | None = None,
) -> IntegrityScanSummary:
    """Scan a finite asset snapshot in bounded keyset-paginated batches."""
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 1000:
        raise ValueError("batch_size must be between 1 and 1000.")

    if session_factory is None:
        from app.db.session import SessionLocal

        session_factory = SessionLocal

    # Use the database clock and a strict bound. Rows created in the same
    # timestamp tick are deferred to the next run, keeping this scan finite.
    with session_factory() as db:
        snapshot_started_at = db.scalar(select(func.now()))
    last_asset_id: uuid.UUID | None = None
    scanned = 0
    skipped = 0
    failed = 0
    status_counts: Counter[str] = Counter()

    while True:
        with session_factory() as db:
            stmt = select(Asset.id).where(Asset.created_at < snapshot_started_at)
            if last_asset_id is not None:
                stmt = stmt.where(Asset.id > last_asset_id)
            batch = list(db.scalars(stmt.order_by(Asset.id).limit(batch_size)).all())

        if not batch:
            break

        for asset_id in batch:
            try:
                result = verify_asset_integrity(
                    asset_id,
                    session_factory=session_factory,
                )
                status_counts[result.status] += 1
                scanned += 1
            except LookupError:
                # The asset may have been deleted after the batch query.
                skipped += 1
            except Exception as exc:
                # Keep processing other assets; never log paths, hashes, or exception text.
                failed += 1
                logger.error(
                    "asset_integrity_scan_asset_error asset_id=%s error_type=%s",
                    asset_id,
                    type(exc).__name__,
                )

        last_asset_id = batch[-1]

    return IntegrityScanSummary(
        scanned=scanned,
        skipped=skipped,
        failed=failed,
        status_counts=dict(status_counts),
        last_asset_id=last_asset_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one finite Asset Integrity Monitoring scan.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Maximum asset IDs loaded per database query (1-1000).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        summary = run_integrity_scan(batch_size=args.batch_size)
    except Exception as exc:
        logger.error("asset_integrity_scan_failed error_type=%s", type(exc).__name__)
        return 1

    logger.info(
        "asset_integrity_scan_completed scanned=%d skipped=%d failed=%d statuses=%s last_asset_id=%s",
        summary.scanned,
        summary.skipped,
        summary.failed,
        summary.status_counts,
        summary.last_asset_id,
    )
    return 1 if summary.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

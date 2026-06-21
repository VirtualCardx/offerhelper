from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from apps.worker.celery_app import celery_app
from src.modules.market_intelligence.domain.entities import MarketSalarySnapshot
from src.modules.market_intelligence.infrastructure.repositories import MarketSalaryRepository
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="market.sync_snapshot")
def sync_market_snapshot(
    *,
    position_id: str,
    city: str,
    p25: str,
    p50: str,
    p75: str,
    source: str,
) -> dict[str, str]:
    init_db()
    session = SessionLocal()
    try:
        repository = MarketSalaryRepository(session)
        snapshot = repository.create(
            MarketSalarySnapshot(
                id=str(uuid.uuid4()),
                position_id=position_id,
                city=city,
                p25=Decimal(p25),
                p50=Decimal(p50),
                p75=Decimal(p75),
                source=source,
                update_time=datetime.now(timezone.utc),
            )
        )
        return {
            "snapshotId": snapshot.id,
            "positionId": snapshot.position_id,
            "city": snapshot.city,
            "status": "completed",
        }
    finally:
        session.close()


@celery_app.task(name="market.sync_batch")
def sync_market_snapshot_batch(records: list[dict[str, str]]) -> dict[str, object]:
    results: list[dict[str, str]] = []
    for record in records:
        results.append(
            sync_market_snapshot(
                position_id=record["position_id"],
                city=record["city"],
                p25=record["p25"],
                p50=record["p50"],
                p75=record["p75"],
                source=record["source"],
            )
        )
    return {
        "status": "completed",
        "count": len(results),
        "results": results,
    }


@celery_app.task(name="market.sync_demo_batch")
def sync_demo_market_batch() -> dict[str, object]:
    return {
        "status": "completed",
        "count": 0,
        "results": [],
        "message": "Beat schedule is configured; replace with real upstream market sync pipeline.",
    }

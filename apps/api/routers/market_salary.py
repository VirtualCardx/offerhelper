from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.market_intelligence.domain.entities import MarketSalarySnapshot
from src.modules.market_intelligence.infrastructure.repositories import MarketSalaryRepository
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/market-salary", tags=["Market Salary"])


class MarketSalaryCreateRequest(BaseModel):
    position_id: str = Field(alias="positionId")
    city: str
    p25: Decimal = Field(alias="P25")
    p50: Decimal = Field(alias="P50")
    p75: Decimal = Field(alias="P75")
    source: str


class MarketSalaryUpdateRequest(BaseModel):
    position_id: str = Field(alias="positionId")
    city: str
    p25: Decimal = Field(alias="P25")
    p50: Decimal = Field(alias="P50")
    p75: Decimal = Field(alias="P75")
    source: str


class MarketSalaryResponse(BaseModel):
    id: str
    position_id: str = Field(alias="positionId")
    city: str
    p25: Decimal = Field(alias="P25")
    p50: Decimal = Field(alias="P50")
    p75: Decimal = Field(alias="P75")
    source: str
    update_time: datetime = Field(alias="updateTime")


def _to_response(snapshot: MarketSalarySnapshot) -> MarketSalaryResponse:
    return MarketSalaryResponse(
        id=snapshot.id,
        positionId=snapshot.position_id,
        city=snapshot.city,
        P25=snapshot.p25,
        P50=snapshot.p50,
        P75=snapshot.p75,
        source=snapshot.source,
        updateTime=snapshot.update_time,
    )


@router.post("", response_model=MarketSalaryResponse)
async def create_market_salary(
    request: MarketSalaryCreateRequest,
    session: Session = Depends(get_db_session),
) -> MarketSalaryResponse:
    repository = MarketSalaryRepository(session)
    snapshot = repository.create(
        MarketSalarySnapshot(
            id=str(uuid.uuid4()),
            position_id=request.position_id,
            city=request.city,
            p25=request.p25,
            p50=request.p50,
            p75=request.p75,
            source=request.source,
            update_time=datetime.now(timezone.utc),
        )
    )
    return _to_response(snapshot)


@router.get("", response_model=MarketSalaryResponse)
async def get_market_salary(
    position_id: str = Query(alias="positionId"),
    city: str = Query(...),
    session: Session = Depends(get_db_session),
) -> MarketSalaryResponse:
    repository = MarketSalaryRepository(session)
    return _to_response(repository.get_latest(position_id, city))


@router.get("/history", response_model=list[MarketSalaryResponse])
async def list_market_salary_history(
    position_id: str = Query(alias="positionId"),
    city: str = Query(...),
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> list[MarketSalaryResponse]:
    repository = MarketSalaryRepository(session)
    return [_to_response(snapshot) for snapshot in repository.list_by_scope(position_id, city, limit=limit)]


@router.post("/{snapshot_id}/promote", response_model=MarketSalaryResponse)
async def promote_market_salary(
    snapshot_id: str,
    session: Session = Depends(get_db_session),
) -> MarketSalaryResponse:
    repository = MarketSalaryRepository(session)
    snapshot = repository.promote(snapshot_id, update_time=datetime.now(timezone.utc))
    return _to_response(snapshot)


@router.patch("/{snapshot_id}", response_model=MarketSalaryResponse)
async def update_market_salary(
    snapshot_id: str,
    request: MarketSalaryUpdateRequest,
    session: Session = Depends(get_db_session),
) -> MarketSalaryResponse:
    repository = MarketSalaryRepository(session)
    snapshot = repository.update(
        snapshot_id,
        position_id=request.position_id,
        city=request.city,
        p25=request.p25,
        p50=request.p50,
        p75=request.p75,
        source=request.source,
        update_time=datetime.now(timezone.utc),
    )
    return _to_response(snapshot)


@router.delete("/{snapshot_id}", status_code=204)
async def delete_market_salary(
    snapshot_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    repository = MarketSalaryRepository(session)
    repository.delete(snapshot_id)

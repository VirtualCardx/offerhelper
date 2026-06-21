from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.modules.market_intelligence.domain.entities import MarketSalarySnapshot
from src.modules.market_intelligence.infrastructure.models import MarketSalaryModel
from src.shared.presentation.errors import DomainValidationError


class MarketSalaryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, snapshot: MarketSalarySnapshot) -> MarketSalarySnapshot:
        record = MarketSalaryModel(
            id=snapshot.id,
            position_id=snapshot.position_id,
            city=snapshot.city,
            p25=snapshot.p25,
            p50=snapshot.p50,
            p75=snapshot.p75,
            source=snapshot.source,
            update_time=snapshot.update_time,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def get_latest(self, position_id: str, city: str) -> MarketSalarySnapshot:
        stmt = (
            select(MarketSalaryModel)
            .where(MarketSalaryModel.position_id == position_id, MarketSalaryModel.city == city)
            .order_by(desc(MarketSalaryModel.update_time), desc(MarketSalaryModel.id))
            .limit(1)
        )
        record = self.session.execute(stmt).scalars().first()
        if record is None:
            raise DomainValidationError(
                f"No market salary snapshot found for position '{position_id}' in city '{city}'."
            )
        return self._to_domain(record)

    def list_by_scope(
        self,
        position_id: str,
        city: str,
        *,
        limit: int = 20,
    ) -> list[MarketSalarySnapshot]:
        stmt = (
            select(MarketSalaryModel)
            .where(MarketSalaryModel.position_id == position_id, MarketSalaryModel.city == city)
            .order_by(desc(MarketSalaryModel.update_time), desc(MarketSalaryModel.id))
            .limit(limit)
        )
        records = self.session.execute(stmt).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_by_id(self, snapshot_id: str) -> MarketSalarySnapshot:
        record = self.session.get(MarketSalaryModel, snapshot_id)
        if record is None:
            raise DomainValidationError(f"Market salary snapshot '{snapshot_id}' does not exist.")
        return self._to_domain(record)

    def update(
        self,
        snapshot_id: str,
        *,
        position_id: str,
        city: str,
        p25: Decimal,
        p50: Decimal,
        p75: Decimal,
        source: str,
        update_time: datetime,
    ) -> MarketSalarySnapshot:
        record = self.session.get(MarketSalaryModel, snapshot_id)
        if record is None:
            raise DomainValidationError(f"Market salary snapshot '{snapshot_id}' does not exist.")
        record.position_id = position_id
        record.city = city
        record.p25 = p25
        record.p50 = p50
        record.p75 = p75
        record.source = source
        record.update_time = update_time
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def promote(self, snapshot_id: str, *, update_time: datetime) -> MarketSalarySnapshot:
        source_record = self.session.get(MarketSalaryModel, snapshot_id)
        if source_record is None:
            raise DomainValidationError(f"Market salary snapshot '{snapshot_id}' does not exist.")

        promoted_record = MarketSalaryModel(
            id=str(uuid4()),
            position_id=source_record.position_id,
            city=source_record.city,
            p25=source_record.p25,
            p50=source_record.p50,
            p75=source_record.p75,
            source=source_record.source,
            update_time=update_time,
        )
        self.session.add(promoted_record)
        self.session.commit()
        self.session.refresh(promoted_record)
        return self._to_domain(promoted_record)

    def delete(self, snapshot_id: str) -> None:
        record = self.session.get(MarketSalaryModel, snapshot_id)
        if record is None:
            raise DomainValidationError(f"Market salary snapshot '{snapshot_id}' does not exist.")
        self.session.delete(record)
        self.session.commit()

    @staticmethod
    def _to_domain(record: MarketSalaryModel) -> MarketSalarySnapshot:
        return MarketSalarySnapshot(
            id=record.id,
            position_id=record.position_id,
            city=record.city,
            p25=Decimal(record.p25),
            p50=Decimal(record.p50),
            p75=Decimal(record.p75),
            source=record.source,
            update_time=datetime.fromisoformat(record.update_time.isoformat()),
        )

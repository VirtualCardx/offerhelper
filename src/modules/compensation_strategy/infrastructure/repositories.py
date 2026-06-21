from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.compensation_strategy.domain.services import CRFactor
from src.modules.compensation_strategy.infrastructure.models import (
    CompensationStrategyFactorModel,
    CompensationStrategyModel,
)
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class CompensationStrategy:
    id: str
    company_id: str
    name: str
    budget_policy: dict[str, Decimal]
    factors: list[CRFactor]


class CompensationStrategyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        company_id: str,
        name: str,
        budget_policy: dict[str, Decimal],
        factors: list[CRFactor],
    ) -> CompensationStrategy:
        strategy = CompensationStrategyModel(
            id=str(uuid.uuid4()),
            company_id=company_id,
            name=name,
            budget_policy_json=json.dumps({key: str(value) for key, value in budget_policy.items()}),
        )
        self.session.add(strategy)
        self.session.flush()

        for index, factor in enumerate(factors):
            self.session.add(
                CompensationStrategyFactorModel(
                    strategy_id=strategy.id,
                    factor_code=factor.factor_code,
                    weight=factor.weight,
                    min_value=factor.min_value,
                    target_value=factor.target_value,
                    max_value=factor.max_value,
                    priority=index,
                )
            )

        self.session.commit()
        self.session.refresh(strategy)
        return self.get_by_id(strategy.id)

    def update(
        self,
        strategy_id: str,
        *,
        name: str,
        budget_policy: dict[str, Decimal],
        factors: list[CRFactor],
    ) -> CompensationStrategy:
        strategy = self.session.get(CompensationStrategyModel, strategy_id)
        if strategy is None:
            raise DomainValidationError(f"Compensation strategy '{strategy_id}' does not exist.")

        strategy.name = name
        strategy.budget_policy_json = json.dumps({key: str(value) for key, value in budget_policy.items()})
        strategy.factors.clear()
        self.session.flush()

        for index, factor in enumerate(factors):
            strategy.factors.append(
                CompensationStrategyFactorModel(
                    strategy_id=strategy.id,
                    factor_code=factor.factor_code,
                    weight=factor.weight,
                    min_value=factor.min_value,
                    target_value=factor.target_value,
                    max_value=factor.max_value,
                    priority=index,
                )
            )

        self.session.commit()
        self.session.refresh(strategy)
        return self.get_by_id(strategy.id)

    def get_by_id(self, strategy_id: str) -> CompensationStrategy:
        strategy = self.session.get(CompensationStrategyModel, strategy_id)
        if strategy is None:
            raise DomainValidationError(f"Compensation strategy '{strategy_id}' does not exist.")
        factor_models = sorted(strategy.factors, key=lambda item: item.priority)
        budget_policy_raw = json.loads(strategy.budget_policy_json)
        return CompensationStrategy(
            id=strategy.id,
            company_id=strategy.company_id,
            name=strategy.name,
            budget_policy={key: Decimal(value) for key, value in budget_policy_raw.items()},
            factors=[
                CRFactor(
                    factor_code=factor.factor_code,
                    weight=Decimal(factor.weight),
                    min_value=Decimal(factor.min_value),
                    target_value=Decimal(factor.target_value),
                    max_value=Decimal(factor.max_value),
                )
                for factor in factor_models
            ],
        )

    def list_strategies(
        self,
        *,
        company_id: str | None = None,
        limit: int = 100,
    ) -> list[CompensationStrategy]:
        query = self.session.query(CompensationStrategyModel)
        if company_id is not None:
            query = query.filter(CompensationStrategyModel.company_id == company_id)
        records = query.order_by(CompensationStrategyModel.created_at.desc()).limit(limit).all()
        return [self.get_by_id(item.id) for item in records]

    def delete(self, strategy_id: str) -> None:
        strategy = self.session.get(CompensationStrategyModel, strategy_id)
        if strategy is None:
            raise DomainValidationError(f"Compensation strategy '{strategy_id}' does not exist.")
        self.session.delete(strategy)
        self.session.commit()

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.compensation_strategy.domain.services import CRFactor
from src.modules.compensation_strategy.infrastructure.repositories import (
    CompensationStrategy,
    CompensationStrategyRepository,
)
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/compensation-strategies", tags=["Compensation Strategies"])


class StrategyFactorRequest(BaseModel):
    factor_code: str = Field(alias="factorCode")
    weight: Decimal
    min_value: Decimal = Field(alias="min")
    target_value: Decimal = Field(alias="target")
    max_value: Decimal = Field(alias="max")


class BudgetPolicyRequest(BaseModel):
    limit: Decimal
    yellow_threshold: Decimal = Field(default=Decimal("1.00"), alias="yellowThreshold")
    red_threshold: Decimal = Field(default=Decimal("1.10"), alias="redThreshold")


class CompensationStrategyCreateRequest(BaseModel):
    company_id: str = Field(alias="companyId")
    name: str
    budget_policy: BudgetPolicyRequest = Field(alias="budgetPolicy")
    factors: list[StrategyFactorRequest]


class CompensationStrategyUpdateRequest(BaseModel):
    name: str
    budget_policy: BudgetPolicyRequest = Field(alias="budgetPolicy")
    factors: list[StrategyFactorRequest]


class StrategyFactorResponse(BaseModel):
    factor_code: str = Field(alias="factorCode")
    weight: Decimal
    min_value: Decimal = Field(alias="min")
    target_value: Decimal = Field(alias="target")
    max_value: Decimal = Field(alias="max")


class BudgetPolicyResponse(BaseModel):
    limit: Decimal
    yellow_threshold: Decimal = Field(alias="yellowThreshold")
    red_threshold: Decimal = Field(alias="redThreshold")


class CompensationStrategyResponse(BaseModel):
    id: str
    company_id: str = Field(alias="companyId")
    name: str
    budget_policy: BudgetPolicyResponse = Field(alias="budgetPolicy")
    factors: list[StrategyFactorResponse]


def _to_response(strategy: CompensationStrategy) -> CompensationStrategyResponse:
    return CompensationStrategyResponse(
        id=strategy.id,
        companyId=strategy.company_id,
        name=strategy.name,
        budgetPolicy=BudgetPolicyResponse(
            limit=strategy.budget_policy["limit"],
            yellowThreshold=strategy.budget_policy.get("yellow_threshold", Decimal("1.00")),
            redThreshold=strategy.budget_policy.get("red_threshold", Decimal("1.10")),
        ),
        factors=[
            StrategyFactorResponse(
                factorCode=factor.factor_code,
                weight=factor.weight,
                min=factor.min_value,
                target=factor.target_value,
                max=factor.max_value,
            )
            for factor in strategy.factors
        ],
    )


@router.post("", response_model=CompensationStrategyResponse)
async def create_compensation_strategy(
    request: CompensationStrategyCreateRequest,
    session: Session = Depends(get_db_session),
) -> CompensationStrategyResponse:
    repository = CompensationStrategyRepository(session)
    strategy = repository.create(
        company_id=request.company_id,
        name=request.name,
        budget_policy={
            "limit": request.budget_policy.limit,
            "yellow_threshold": request.budget_policy.yellow_threshold,
            "red_threshold": request.budget_policy.red_threshold,
        },
        factors=[
            CRFactor(
                factor_code=factor.factor_code,
                weight=factor.weight,
                min_value=factor.min_value,
                target_value=factor.target_value,
                max_value=factor.max_value,
            )
            for factor in request.factors
        ],
    )
    return _to_response(strategy)


@router.get("/{strategy_id}", response_model=CompensationStrategyResponse)
async def get_compensation_strategy(
    strategy_id: str,
    session: Session = Depends(get_db_session),
) -> CompensationStrategyResponse:
    repository = CompensationStrategyRepository(session)
    return _to_response(repository.get_by_id(strategy_id))


@router.get("", response_model=list[CompensationStrategyResponse])
async def list_compensation_strategies(
    company_id: str | None = Query(default=None, alias="companyId"),
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[CompensationStrategyResponse]:
    repository = CompensationStrategyRepository(session)
    return [
        _to_response(item)
        for item in repository.list_strategies(company_id=company_id, limit=limit)
    ]


@router.patch("/{strategy_id}", response_model=CompensationStrategyResponse)
async def update_compensation_strategy(
    strategy_id: str,
    request: CompensationStrategyUpdateRequest,
    session: Session = Depends(get_db_session),
) -> CompensationStrategyResponse:
    repository = CompensationStrategyRepository(session)
    strategy = repository.update(
        strategy_id,
        name=request.name,
        budget_policy={
            "limit": request.budget_policy.limit,
            "yellow_threshold": request.budget_policy.yellow_threshold,
            "red_threshold": request.budget_policy.red_threshold,
        },
        factors=[
            CRFactor(
                factor_code=factor.factor_code,
                weight=factor.weight,
                min_value=factor.min_value,
                target_value=factor.target_value,
                max_value=factor.max_value,
            )
            for factor in request.factors
        ],
    )
    return _to_response(strategy)


@router.delete("/{strategy_id}", status_code=204)
async def delete_compensation_strategy(
    strategy_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    repository = CompensationStrategyRepository(session)
    repository.delete(strategy_id)

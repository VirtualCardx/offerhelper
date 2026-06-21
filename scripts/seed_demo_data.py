from __future__ import annotations

import pathlib
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.candidate.infrastructure.models import CandidateModel
from src.modules.compensation_strategy.infrastructure.models import (
    CompensationStrategyFactorModel,
    CompensationStrategyModel,
)
from src.modules.market_intelligence.infrastructure.models import MarketSalaryModel
from src.modules.offer_decision.infrastructure.models import OfferModel, OfferRiskAssessmentModel
from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel
from src.modules.pay_equity.infrastructure.models import EmployeeSalaryModel
from src.shared.infrastructure.db.session import SessionLocal, init_db


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        company = session.execute(
            select(CompanyModel).where(CompanyModel.tenant_code == "demo-tenant")
        ).scalar_one_or_none()
        if company is None:
            company = CompanyModel(
                id=str(uuid.uuid4()),
                name="Demo Company",
                industry="Internet",
                tenant_code="demo-tenant",
            )
            session.add(company)
            session.flush()

        department = session.execute(
            select(DepartmentModel).where(
                DepartmentModel.company_id == company.id,
                DepartmentModel.name == "Growth",
            )
        ).scalar_one_or_none()
        if department is None:
            department = DepartmentModel(
                id=str(uuid.uuid4()),
                company_id=company.id,
                name="Growth",
                domain="Growth",
            )
            session.add(department)
            session.flush()

        position = session.execute(
            select(PositionModel).where(
                PositionModel.company_id == company.id,
                PositionModel.title == "Growth Manager",
            )
        ).scalar_one_or_none()
        if position is None:
            position = PositionModel(
                id=str(uuid.uuid4()),
                company_id=company.id,
                title="Growth Manager",
                job_family="Marketing",
                level_band="P6",
            )
            session.add(position)
            session.flush()

        existing_salary = session.execute(
            select(EmployeeSalaryModel).where(
                EmployeeSalaryModel.company_id == company.id,
                EmployeeSalaryModel.department_id == department.id,
                EmployeeSalaryModel.level == "P6",
            )
        ).scalars().first()
        if existing_salary is None:
            session.add_all(
                [
                    EmployeeSalaryModel(
                        id=str(uuid.uuid4()),
                        company_id=company.id,
                        department_id=department.id,
                        position_id=position.id,
                        level="P6",
                        salary=35000,
                    ),
                    EmployeeSalaryModel(
                        id=str(uuid.uuid4()),
                        company_id=company.id,
                        department_id=department.id,
                        position_id=position.id,
                        level="P6",
                        salary=37000,
                    ),
                ]
            )
            session.flush()

        market_snapshot = session.execute(
            select(MarketSalaryModel).where(
                MarketSalaryModel.position_id == position.id,
                MarketSalaryModel.city == "Shanghai",
            )
        ).scalar_one_or_none()
        if market_snapshot is None:
            session.add(
                MarketSalaryModel(
                    id=str(uuid.uuid4()),
                    position_id=position.id,
                    city="Shanghai",
                    p25=Decimal("25000"),
                    p50=Decimal("35000"),
                    p75=Decimal("45000"),
                    source="seed-demo",
                )
            )
            session.flush()

        strategy = session.execute(
            select(CompensationStrategyModel).where(
                CompensationStrategyModel.company_id == company.id,
                CompensationStrategyModel.name == "Default 2026 Strategy",
            )
        ).scalar_one_or_none()
        if strategy is None:
            strategy = CompensationStrategyModel(
                id=str(uuid.uuid4()),
                company_id=company.id,
                name="Default 2026 Strategy",
                budget_policy_json='{"limit": "40000", "yellowThreshold": "1.0", "redThreshold": "1.1"}',
            )
            session.add(strategy)
            session.flush()
            session.add_all(
                [
                    CompensationStrategyFactorModel(
                        id=str(uuid.uuid4()),
                        strategy_id=strategy.id,
                        factor_code="company",
                        weight=Decimal("0.3000"),
                        min_value=Decimal("0.8000"),
                        target_value=Decimal("1.0000"),
                        max_value=Decimal("1.1000"),
                        priority=0,
                    ),
                    CompensationStrategyFactorModel(
                        id=str(uuid.uuid4()),
                        strategy_id=strategy.id,
                        factor_code="domain",
                        weight=Decimal("0.3000"),
                        min_value=Decimal("0.9000"),
                        target_value=Decimal("1.0500"),
                        max_value=Decimal("1.2000"),
                        priority=1,
                    ),
                    CompensationStrategyFactorModel(
                        id=str(uuid.uuid4()),
                        strategy_id=strategy.id,
                        factor_code="department",
                        weight=Decimal("0.2000"),
                        min_value=Decimal("0.9500"),
                        target_value=Decimal("1.0000"),
                        max_value=Decimal("1.1500"),
                        priority=2,
                    ),
                    CompensationStrategyFactorModel(
                        id=str(uuid.uuid4()),
                        strategy_id=strategy.id,
                        factor_code="talent",
                        weight=Decimal("0.2000"),
                        min_value=Decimal("1.0000"),
                        target_value=Decimal("1.1500"),
                        max_value=Decimal("1.3000"),
                        priority=3,
                    ),
                ]
            )
            session.flush()

        historical_candidates = [
            {
                "name": "Alice Historical",
                "current_salary": Decimal("30000"),
                "expected_salary": Decimal("38000"),
                "years_experience": 5,
                "interview_score": 88,
                "has_other_offer": False,
                "recommended_salary": Decimal("36000"),
                "accept_probability": Decimal("0.79"),
                "outcome_status": "ACCEPTED",
            },
            {
                "name": "Bob Historical",
                "current_salary": Decimal("32000"),
                "expected_salary": Decimal("36000"),
                "years_experience": 6,
                "interview_score": 76,
                "has_other_offer": True,
                "recommended_salary": Decimal("33500"),
                "accept_probability": Decimal("0.43"),
                "outcome_status": "REJECTED",
            },
            {
                "name": "Cindy Historical",
                "current_salary": Decimal("29000"),
                "expected_salary": Decimal("40000"),
                "years_experience": 7,
                "interview_score": 94,
                "has_other_offer": True,
                "recommended_salary": Decimal("39200"),
                "accept_probability": Decimal("0.82"),
                "outcome_status": "ACCEPTED",
            },
            {
                "name": "Dylan Historical",
                "current_salary": Decimal("34000"),
                "expected_salary": Decimal("39000"),
                "years_experience": 6,
                "interview_score": 79,
                "has_other_offer": True,
                "recommended_salary": Decimal("35000"),
                "accept_probability": Decimal("0.47"),
                "outcome_status": "REJECTED",
            },
        ]

        for index, candidate_seed in enumerate(historical_candidates):
            candidate = session.execute(
                select(CandidateModel).where(
                    CandidateModel.company_id == company.id,
                    CandidateModel.name == candidate_seed["name"],
                )
            ).scalar_one_or_none()
            if candidate is None:
                candidate = CandidateModel(
                    id=str(uuid.uuid4()),
                    company_id=company.id,
                    department_id=department.id,
                    position_id=position.id,
                    name=str(candidate_seed["name"]),
                    current_salary=Decimal(candidate_seed["current_salary"]),
                    expected_salary=Decimal(candidate_seed["expected_salary"]),
                    years_experience=int(candidate_seed["years_experience"]),
                    level="P6",
                    skills="Growth,SQL,CRM",
                    interview_score=int(candidate_seed["interview_score"]),
                    has_other_offer=bool(candidate_seed["has_other_offer"]),
                    city="Shanghai",
                )
                session.add(candidate)
                session.flush()

            offer = session.execute(
                select(OfferModel).where(
                    OfferModel.candidate_id == candidate.id,
                    OfferModel.strategy_id == strategy.id,
                )
            ).scalar_one_or_none()
            if offer is None:
                recommended_salary = Decimal(candidate_seed["recommended_salary"])
                decided_at = datetime.now(timezone.utc) - timedelta(days=30 - (index * 5))
                offer = OfferModel(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate.id,
                    strategy_id=strategy.id,
                    recommended_salary=recommended_salary,
                    range_min=(recommended_salary * Decimal("0.95")).quantize(Decimal("0.01")),
                    range_max=(recommended_salary * Decimal("1.05")).quantize(Decimal("0.01")),
                    cr_value=Decimal("1.0450"),
                    accept_probability=Decimal(candidate_seed["accept_probability"]),
                    acceptance_model_version="0.2.0",
                    competitiveness_score=78,
                    confidence=Decimal("0.83"),
                    budget_usage_ratio=(recommended_salary / Decimal("40000")).quantize(Decimal("0.0001")),
                    budget_risk_level="LOW",
                    equity_score=72,
                    equity_risk_level="LOW",
                    equity_p25=Decimal("35000"),
                    equity_p50=Decimal("36000"),
                    equity_p75=Decimal("37000"),
                    inversion_detected=0,
                    equity_message="Seeded historical offer within expected range",
                    overall_risk_level="LOW",
                    outcome_status=str(candidate_seed["outcome_status"]),
                    outcome_notes="seed-demo historical decision",
                    decided_at=decided_at,
                )
                session.add(offer)
                session.flush()
                session.add(
                    OfferRiskAssessmentModel(
                        id=str(uuid.uuid4()),
                        offer_id=offer.id,
                        reasons="seeded_historical_offer",
                    )
                )
                session.flush()

        session.commit()
        print(
            {
                "companyId": company.id,
                "departmentId": department.id,
                "positionId": position.id,
                "strategyId": strategy.id,
            }
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()

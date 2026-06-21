from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.modules.acceptance_prediction.application.training_data import HistoricalAcceptanceTrainingDataService
from src.modules.candidate.infrastructure.models import CandidateModel
from src.modules.compensation_strategy.infrastructure.models import (
    CompensationStrategyFactorModel,
    CompensationStrategyModel,
)
from src.modules.market_intelligence.infrastructure.models import MarketSalaryModel
from src.modules.offer_decision.infrastructure.models import OfferModel, OfferRiskAssessmentModel
from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel
from src.shared.infrastructure.db.base import Base


def test_build_training_samples_from_completed_offers() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    company_id = str(uuid.uuid4())
    department_id = str(uuid.uuid4())
    position_id = str(uuid.uuid4())
    strategy_id = str(uuid.uuid4())
    candidate_id = str(uuid.uuid4())
    offer_id = str(uuid.uuid4())

    with SessionLocal() as session:
        session.add(CompanyModel(id=company_id, name="Test Company", industry="Internet", tenant_code="test-tenant"))
        session.add(DepartmentModel(id=department_id, company_id=company_id, name="Growth", domain="Growth"))
        session.add(
            PositionModel(
                id=position_id,
                company_id=company_id,
                title="Growth Manager",
                job_family="Marketing",
                level_band="P6",
            )
        )
        session.add(
            MarketSalaryModel(
                id=str(uuid.uuid4()),
                position_id=position_id,
                city="Shanghai",
                p25=Decimal("25000"),
                p50=Decimal("35000"),
                p75=Decimal("45000"),
                source="unit-test",
            )
        )
        session.add(
            CompensationStrategyModel(
                id=strategy_id,
                company_id=company_id,
                name="Default 2026 Strategy",
                budget_policy_json=json.dumps({"limit": "40000"}),
            )
        )
        session.add(
            CompensationStrategyFactorModel(
                id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                factor_code="company",
                weight=Decimal("1.0000"),
                min_value=Decimal("1.0000"),
                target_value=Decimal("1.0000"),
                max_value=Decimal("1.0000"),
                priority=0,
            )
        )
        session.add(
            CandidateModel(
                id=candidate_id,
                company_id=company_id,
                department_id=department_id,
                position_id=position_id,
                name="Alice",
                current_salary=Decimal("30000"),
                expected_salary=Decimal("38000"),
                years_experience=5,
                level="P6",
                skills="Growth,SQL",
                interview_score=90,
                has_other_offer=True,
                city="Shanghai",
            )
        )
        session.add(
            OfferModel(
                id=offer_id,
                candidate_id=candidate_id,
                strategy_id=strategy_id,
                recommended_salary=Decimal("39501.00"),
                range_min=Decimal("37525.95"),
                range_max=Decimal("41476.05"),
                cr_value=Decimal("1.0450"),
                accept_probability=Decimal("0.81"),
                acceptance_model_version="0.3.0",
                competitiveness_score=84,
                confidence=Decimal("0.83"),
                budget_usage_ratio=Decimal("0.9875"),
                budget_risk_level="LOW",
                equity_score=70,
                equity_risk_level="LOW",
                equity_p25=Decimal("35000"),
                equity_p50=Decimal("36000"),
                equity_p75=Decimal("37000"),
                inversion_detected=0,
                equity_message="within range",
                overall_risk_level="LOW",
                outcome_status="ACCEPTED",
                outcome_notes="signed",
                decided_at=datetime.now(timezone.utc),
            )
        )
        session.add(
            OfferRiskAssessmentModel(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                reasons="unit_test",
            )
        )
        session.commit()

        samples = HistoricalAcceptanceTrainingDataService(session).build_training_samples()

    Base.metadata.drop_all(bind=engine)

    assert len(samples) == 1
    assert samples[0].accepted is True
    assert samples[0].current_salary == Decimal("30000")
    assert samples[0].market_p50 == Decimal("35000")

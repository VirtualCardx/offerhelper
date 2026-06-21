from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.config.settings import get_settings


settings = get_settings()

engine_kwargs: dict[str, object] = {"echo": False}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from src.modules.acceptance_prediction.infrastructure.models import (
        MLGovernanceEventModel,
        MLModelVersionModel,
        MLTrainingRunModel,
    )
    from src.modules.candidate.infrastructure.models import CandidateModel
    from src.modules.compensation_strategy.infrastructure.models import (
        CompensationStrategyFactorModel,
        CompensationStrategyModel,
    )
    from src.modules.market_intelligence.infrastructure.models import MarketSalaryModel
    from src.modules.offer_decision.infrastructure.models import (
        OfferModel,
        OfferReportModel,
        OfferRiskAssessmentModel,
    )
    from src.modules.org.infrastructure.models import (
        CompanyModel,
        DepartmentModel,
        PositionModel,
    )
    from src.modules.pay_equity.infrastructure.models import EmployeeSalaryModel
    from src.shared.infrastructure.db.base import Base

    _ = (
        CandidateModel,
        MLModelVersionModel,
        MLTrainingRunModel,
        MLGovernanceEventModel,
        CompensationStrategyFactorModel,
        CompensationStrategyModel,
        MarketSalaryModel,
        EmployeeSalaryModel,
        OfferModel,
        OfferReportModel,
        OfferRiskAssessmentModel,
        CompanyModel,
        DepartmentModel,
        PositionModel,
    )
    Base.metadata.create_all(bind=engine)

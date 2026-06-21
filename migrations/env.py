from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

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
from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel
from src.modules.pay_equity.infrastructure.models import EmployeeSalaryModel
from src.shared.config.settings import get_settings
from src.shared.infrastructure.db.base import Base


config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
_ = (
    CandidateModel,
    MLModelVersionModel,
    MLTrainingRunModel,
    MLGovernanceEventModel,
    CompanyModel,
    CompensationStrategyFactorModel,
    CompensationStrategyModel,
    DepartmentModel,
    EmployeeSalaryModel,
    MarketSalaryModel,
    OfferModel,
    OfferReportModel,
    OfferRiskAssessmentModel,
    PositionModel,
)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.candidate.infrastructure.repositories import CandidateRepository
from src.modules.compensation_strategy.infrastructure.repositories import CompensationStrategyRepository
from src.modules.market_intelligence.infrastructure.repositories import MarketSalaryRepository
from src.modules.offer_decision.infrastructure.repositories import OfferRepository
from src.modules.report_engine.domain.services import OfferReportService
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportGenerateResponse(BaseModel):
    report_id: str = Field(alias="reportId")
    offer_id: str = Field(alias="offerId")
    format: str
    content: str


@router.post("/offers/{offer_id}/generate", response_model=ReportGenerateResponse)
async def generate_offer_report(
    offer_id: str,
    session: Session = Depends(get_db_session),
) -> ReportGenerateResponse:
    offer_repository = OfferRepository(session)
    candidate_repository = CandidateRepository(session)
    strategy_repository = CompensationStrategyRepository(session)
    market_repository = MarketSalaryRepository(session)
    report_service = OfferReportService()

    offer = offer_repository.get_by_id(offer_id)
    candidate = candidate_repository.get_by_id(offer.candidate_id)
    strategy = strategy_repository.get_by_id(offer.strategy_id)
    market = market_repository.get_latest(candidate.position_id, candidate.city)

    markdown = report_service.generate_markdown(
        candidate_name=candidate.name,
        level=candidate.level,
        city=candidate.city,
        market_p50=str(market.p50),
        market_p75=str(market.p75),
        strategy_name=strategy.name,
        recommended_offer=str(offer.recommended_salary),
        cr_value=str(offer.cr_value),
        accept_probability=str(offer.accept_probability),
        budget_risk=offer.budget_risk_level,
        equity_risk=offer.equity_risk_level,
        equity_message=offer.equity_message,
        overall_risk=offer.overall_risk_level,
        risk_reasons=offer.risk_reasons,
    )
    report_id = offer_repository.save_report(offer_id=offer_id, content=markdown)

    return ReportGenerateResponse(
        reportId=report_id,
        offerId=offer_id,
        format="markdown",
        content=markdown,
    )

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.acceptance_prediction.application.exporter import AcceptanceTrainingSample
from src.modules.candidate.infrastructure.models import CandidateModel
from src.modules.market_intelligence.infrastructure.repositories import MarketSalaryRepository
from src.modules.offer_decision.infrastructure.models import OfferModel
from src.shared.presentation.errors import DomainValidationError


class HistoricalAcceptanceTrainingDataService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.market_repository = MarketSalaryRepository(session)

    def build_training_samples(self) -> list[AcceptanceTrainingSample]:
        stmt = (
            select(OfferModel, CandidateModel)
            .join(CandidateModel, CandidateModel.id == OfferModel.candidate_id)
            .where(OfferModel.outcome_status.in_(("ACCEPTED", "REJECTED")))
            .order_by(OfferModel.decided_at.asc().nulls_last(), OfferModel.created_at.asc())
        )
        rows = self.session.execute(stmt).all()
        if not rows:
            raise DomainValidationError("No completed offers are available for acceptance model training.")

        training_samples: list[AcceptanceTrainingSample] = []
        for offer, candidate in rows:
            market = self.market_repository.get_latest(candidate.position_id, candidate.city)
            training_samples.append(
                AcceptanceTrainingSample(
                    current_salary=candidate.current_salary,
                    recommended_offer=offer.recommended_salary,
                    market_p50=market.p50,
                    interview_score=candidate.interview_score,
                    has_other_offer=candidate.has_other_offer,
                    accepted=offer.outcome_status == "ACCEPTED",
                )
            )
        return training_samples

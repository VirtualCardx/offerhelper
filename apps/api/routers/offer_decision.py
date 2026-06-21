from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.acceptance_prediction.application.registry import ModelRegistryService
from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionInput,
    AcceptancePredictionService,
)
from src.modules.acceptance_prediction.infrastructure.repositories import MLModelVersionRepository
from src.modules.budget_guard.domain.services import BudgetAssessment, BudgetGuardService
from src.modules.candidate.infrastructure.repositories import CandidateRepository
from src.modules.compensation_strategy.domain.services import (
    CRCalculationService,
    CRFactor,
)
from src.modules.compensation_strategy.infrastructure.repositories import CompensationStrategyRepository
from src.modules.market_intelligence.infrastructure.repositories import MarketSalaryRepository
from src.modules.offer_decision.domain.services import (
    OfferDecisionEngine,
    OfferDecisionInput,
)
from src.modules.offer_decision.infrastructure.repositories import OfferRepository
from src.modules.pay_equity.domain.services import EquityResult, PayEquityEngine, PeerSalary
from src.modules.pay_equity.infrastructure.repositories import EmployeeSalaryRepository
from src.modules.risk_engine.domain.services import RiskAssessment, RiskEngine
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/offers", tags=["Offer Decision"])


class CRFactorRequest(BaseModel):
    factor_code: str = Field(alias="factorCode")
    weight: Decimal
    min_value: Decimal = Field(alias="min")
    target_value: Decimal = Field(alias="target")
    max_value: Decimal = Field(alias="max")


class CandidateRequest(BaseModel):
    current_salary: Decimal = Field(alias="currentSalary")
    years_experience: int = Field(alias="yearsExperience")
    level: str
    interview_score: int = Field(alias="interviewScore")
    has_other_offer: bool = Field(alias="hasOtherOffer")


class MarketRequest(BaseModel):
    p50: Decimal = Field(alias="P50")
    p75: Decimal = Field(alias="P75")


class BudgetRequest(BaseModel):
    limit: Decimal


class OfferRecommendationRequest(BaseModel):
    candidate: CandidateRequest
    market: MarketRequest
    budget: BudgetRequest
    factors: list[CRFactorRequest]
    selected_point: Literal["min", "target", "max"] = Field(default="target", alias="selectedPoint")


class CandidateBasedOfferRecommendationRequest(BaseModel):
    candidate_id: str = Field(alias="candidateId")
    budget: BudgetRequest
    factors: list[CRFactorRequest]
    selected_point: Literal["min", "target", "max"] = Field(default="target", alias="selectedPoint")
    city: str | None = None


class OfferRangeResponse(BaseModel):
    min: Decimal
    max: Decimal


class OfferRecommendationResponse(BaseModel):
    recommended_offer: Decimal = Field(alias="recommendedOffer")
    range: OfferRangeResponse
    cr_value: Decimal = Field(alias="crValue")
    accept_probability: Decimal = Field(alias="acceptProbability")
    acceptance_model_version: str = Field(alias="acceptanceModelVersion")
    competitiveness_score: int = Field(alias="competitivenessScore")
    confidence: Decimal
    risk_level: str = Field(alias="riskLevel")
    risk_reasons: list[str] = Field(alias="riskReasons")


class BudgetAssessmentResponse(BaseModel):
    usage_ratio: Decimal = Field(alias="usageRatio")
    risk_level: str = Field(alias="riskLevel")
    exceeded: bool


class EquityAssessmentResponse(BaseModel):
    equity_score: int = Field(alias="equityScore")
    risk_level: str = Field(alias="riskLevel")
    message: str
    p25: Decimal = Field(alias="P25")
    p50: Decimal = Field(alias="P50")
    p75: Decimal = Field(alias="P75")
    inversion_detected: bool = Field(alias="inversionDetected")


class PersistOfferRecommendationRequest(BaseModel):
    candidate_id: str = Field(alias="candidateId")
    strategy_id: str = Field(alias="strategyId")
    selected_point: Literal["min", "target", "max"] = Field(default="target", alias="selectedPoint")
    city: str | None = None


class PersistOfferRecommendationResponse(OfferRecommendationResponse):
    offer_id: str = Field(alias="offerId")
    candidate_id: str = Field(alias="candidateId")
    market_snapshot_id: str | None = Field(default=None, alias="marketSnapshotId")
    strategy_id: str = Field(alias="strategyId")
    outcome_status: str = Field(alias="outcomeStatus")
    outcome_notes: str | None = Field(default=None, alias="outcomeNotes")
    decided_at: datetime | None = Field(default=None, alias="decidedAt")
    budget: BudgetAssessmentResponse
    equity: EquityAssessmentResponse


class OfferDetailResponse(PersistOfferRecommendationResponse):
    report_markdown: str | None = Field(default=None, alias="reportMarkdown")


class UpdateOfferOutcomeRequest(BaseModel):
    outcome_status: Literal["ACCEPTED", "REJECTED"] = Field(alias="outcomeStatus")
    outcome_notes: str | None = Field(default=None, alias="outcomeNotes")


def _build_offer_response(
    *,
    current_salary: Decimal,
    years_experience: int,
    level: str,
    interview_score: int,
    has_other_offer: bool,
    market_p50: Decimal,
    market_p75: Decimal,
    budget_limit: Decimal,
    factors: list[CRFactor],
    selected_point: Literal["min", "target", "max"],
    peer_salaries: list[Decimal] | None = None,
    acceptance_service: AcceptancePredictionService | None = None,
) -> tuple[OfferRecommendationResponse, Decimal, BudgetAssessment, RiskAssessment, EquityResult]:
    _ = (years_experience, level)
    cr_service = CRCalculationService()
    budget_service = BudgetGuardService()
    risk_engine = RiskEngine()
    equity_engine = PayEquityEngine()
    acceptance_service = acceptance_service or AcceptancePredictionService()
    engine = OfferDecisionEngine()

    cr_value = cr_service.calculate(factors=factors, selected_point=selected_point)
    result = engine.recommend(
        OfferDecisionInput(
            current_salary=current_salary,
            market_p50=market_p50,
            market_p75=market_p75,
            cr_value=cr_value,
            interview_score=interview_score,
            has_other_offer=has_other_offer,
            budget_limit=budget_limit,
        )
    )
    budget_assessment = budget_service.assess(budget_limit=budget_limit, proposed_offer=result.raw_offer)
    equity_result = equity_engine.evaluate(
        offer=budget_assessment.capped_offer,
        peers=[] if peer_salaries is None else [PeerSalary(salary=value) for value in peer_salaries],
    )
    risk_assessment = risk_engine.evaluate(
        raise_ratio=result.raise_ratio,
        above_market_p75=budget_assessment.capped_offer > market_p75,
        budget_exceeded=budget_assessment.exceeded,
        budget_usage_ratio=budget_assessment.usage_ratio,
        equity_risk_level=equity_result.risk_level,
        inversion_detected=equity_result.inversion_detected,
    )
    acceptance_prediction = acceptance_service.predict(
        AcceptancePredictionInput(
            current_salary=current_salary,
            recommended_offer=budget_assessment.capped_offer,
            market_p50=market_p50,
            interview_score=interview_score,
            has_other_offer=has_other_offer,
        )
    )

    confidence = result.confidence
    if risk_assessment.overall_risk == "RED":
        confidence = Decimal("0.78")
    elif risk_assessment.overall_risk == "YELLOW":
        confidence = Decimal("0.83")

    response = OfferRecommendationResponse(
        recommendedOffer=budget_assessment.capped_offer,
        range=OfferRangeResponse(
            min=(budget_assessment.capped_offer * Decimal("0.95")).quantize(Decimal("0.01")),
            max=(budget_assessment.capped_offer * Decimal("1.05")).quantize(Decimal("0.01")),
        ),
        crValue=cr_value,
        acceptProbability=acceptance_prediction.probability,
        acceptanceModelVersion=acceptance_prediction.model_version,
        competitivenessScore=result.competitiveness_score,
        confidence=confidence,
        riskLevel=risk_assessment.overall_risk,
        riskReasons=risk_assessment.reasons,
    )
    return response, cr_value, budget_assessment, risk_assessment, equity_result


@router.post("/recommend", response_model=OfferRecommendationResponse)
async def recommend_offer(request: OfferRecommendationRequest) -> OfferRecommendationResponse:
    response, _, _, _, _ = _build_offer_response(
        current_salary=request.candidate.current_salary,
        years_experience=request.candidate.years_experience,
        level=request.candidate.level,
        interview_score=request.candidate.interview_score,
        has_other_offer=request.candidate.has_other_offer,
        market_p50=request.market.p50,
        market_p75=request.market.p75,
        budget_limit=request.budget.limit,
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
        selected_point=request.selected_point,
        acceptance_service=AcceptancePredictionService(),
    )
    return response


@router.post("/recommend/by-candidate", response_model=OfferRecommendationResponse)
async def recommend_offer_by_candidate(
    request: CandidateBasedOfferRecommendationRequest,
    session: Session = Depends(get_db_session),
) -> OfferRecommendationResponse:
    candidate_repository = CandidateRepository(session)
    market_repository = MarketSalaryRepository(session)
    employee_salary_repository = EmployeeSalaryRepository(session)
    model_version_repository = MLModelVersionRepository(session)
    model_registry_service = ModelRegistryService(model_version_repository)
    candidate = candidate_repository.get_by_id(request.candidate_id)
    market = market_repository.get_latest(candidate.position_id, request.city or candidate.city)
    acceptance_service = model_registry_service.get_prediction_service(model_name="baseline-offer-acceptance")
    peer_salaries = [
        peer.salary
        for peer in employee_salary_repository.list_peer_salaries(
            company_id=candidate.company_id,
            department_id=candidate.department_id,
            level=candidate.level,
        )
    ]

    response, _, _, _, _ = _build_offer_response(
        current_salary=candidate.current_salary,
        years_experience=candidate.years_experience,
        level=candidate.level,
        interview_score=candidate.interview_score,
        has_other_offer=candidate.has_other_offer,
        market_p50=market.p50,
        market_p75=market.p75,
        budget_limit=request.budget.limit,
        peer_salaries=peer_salaries,
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
        selected_point=request.selected_point,
        acceptance_service=acceptance_service,
    )
    return response


@router.post("/recommend-and-save", response_model=PersistOfferRecommendationResponse)
async def recommend_and_save_offer(
    request: PersistOfferRecommendationRequest,
    session: Session = Depends(get_db_session),
) -> PersistOfferRecommendationResponse:
    candidate_repository = CandidateRepository(session)
    strategy_repository = CompensationStrategyRepository(session)
    market_repository = MarketSalaryRepository(session)
    employee_salary_repository = EmployeeSalaryRepository(session)
    offer_repository = OfferRepository(session)
    model_version_repository = MLModelVersionRepository(session)
    model_registry_service = ModelRegistryService(model_version_repository)

    candidate = candidate_repository.get_by_id(request.candidate_id)
    strategy = strategy_repository.get_by_id(request.strategy_id)
    market = market_repository.get_latest(candidate.position_id, request.city or candidate.city)
    acceptance_service = model_registry_service.get_prediction_service(model_name="baseline-offer-acceptance")
    peer_salaries = [
        peer.salary
        for peer in employee_salary_repository.list_peer_salaries(
            company_id=candidate.company_id,
            department_id=candidate.department_id,
            level=candidate.level,
        )
    ]

    response, cr_value, budget_assessment, risk_assessment, equity_result = _build_offer_response(
        current_salary=candidate.current_salary,
        years_experience=candidate.years_experience,
        level=candidate.level,
        interview_score=candidate.interview_score,
        has_other_offer=candidate.has_other_offer,
        market_p50=market.p50,
        market_p75=market.p75,
        budget_limit=strategy.budget_policy["limit"],
        factors=strategy.factors,
        selected_point=request.selected_point,
        peer_salaries=peer_salaries,
        acceptance_service=acceptance_service,
    )

    saved_offer = offer_repository.create(
        candidate_id=candidate.id,
        market_snapshot_id=market.id,
        strategy_id=strategy.id,
        recommended_salary=response.recommended_offer,
        range_min=response.range.min,
        range_max=response.range.max,
        cr_value=cr_value,
        accept_probability=response.accept_probability,
        acceptance_model_version=response.acceptance_model_version,
        competitiveness_score=response.competitiveness_score,
        confidence=response.confidence,
        budget_usage_ratio=budget_assessment.usage_ratio,
        budget_risk_level=budget_assessment.risk_level,
        equity_score=equity_result.equity_score,
        equity_risk_level=equity_result.risk_level,
        equity_p25=equity_result.p25,
        equity_p50=equity_result.p50,
        equity_p75=equity_result.p75,
        inversion_detected=equity_result.inversion_detected,
        equity_message=equity_result.message,
        overall_risk_level=risk_assessment.overall_risk,
        risk_reasons=risk_assessment.reasons,
    )

    return PersistOfferRecommendationResponse(
        offerId=saved_offer.id,
        candidateId=saved_offer.candidate_id,
        marketSnapshotId=saved_offer.market_snapshot_id,
        strategyId=saved_offer.strategy_id,
        outcomeStatus=saved_offer.outcome_status,
        outcomeNotes=saved_offer.outcome_notes,
        decidedAt=saved_offer.decided_at,
        recommendedOffer=saved_offer.recommended_salary,
        range=OfferRangeResponse(min=saved_offer.range_min, max=saved_offer.range_max),
        crValue=saved_offer.cr_value,
        acceptProbability=saved_offer.accept_probability.quantize(Decimal("0.01")),
        acceptanceModelVersion=saved_offer.acceptance_model_version,
        competitivenessScore=saved_offer.competitiveness_score,
        confidence=saved_offer.confidence,
        riskLevel=saved_offer.overall_risk_level,
        riskReasons=saved_offer.risk_reasons,
        budget=BudgetAssessmentResponse(
            usageRatio=saved_offer.budget_usage_ratio,
            riskLevel=saved_offer.budget_risk_level,
            exceeded=saved_offer.budget_usage_ratio > Decimal("1.0000"),
        ),
        equity=EquityAssessmentResponse(
            equityScore=saved_offer.equity_score,
            riskLevel=saved_offer.equity_risk_level,
            message=saved_offer.equity_message,
            P25=saved_offer.equity_p25,
            P50=saved_offer.equity_p50,
            P75=saved_offer.equity_p75,
            inversionDetected=saved_offer.inversion_detected,
        ),
    )


@router.get("/{offer_id}", response_model=OfferDetailResponse)
async def get_offer_detail(
    offer_id: str,
    session: Session = Depends(get_db_session),
) -> OfferDetailResponse:
    offer_repository = OfferRepository(session)
    saved_offer = offer_repository.get_by_id(offer_id)

    return OfferDetailResponse(
        offerId=saved_offer.id,
        candidateId=saved_offer.candidate_id,
        marketSnapshotId=saved_offer.market_snapshot_id,
        strategyId=saved_offer.strategy_id,
        outcomeStatus=saved_offer.outcome_status,
        outcomeNotes=saved_offer.outcome_notes,
        decidedAt=saved_offer.decided_at,
        recommendedOffer=saved_offer.recommended_salary,
        range=OfferRangeResponse(min=saved_offer.range_min, max=saved_offer.range_max),
        crValue=saved_offer.cr_value,
        acceptProbability=saved_offer.accept_probability.quantize(Decimal("0.01")),
        acceptanceModelVersion=saved_offer.acceptance_model_version,
        competitivenessScore=saved_offer.competitiveness_score,
        confidence=saved_offer.confidence,
        riskLevel=saved_offer.overall_risk_level,
        riskReasons=saved_offer.risk_reasons,
        budget=BudgetAssessmentResponse(
            usageRatio=saved_offer.budget_usage_ratio,
            riskLevel=saved_offer.budget_risk_level,
            exceeded=saved_offer.budget_usage_ratio > Decimal("1.0000"),
        ),
        equity=EquityAssessmentResponse(
            equityScore=saved_offer.equity_score,
            riskLevel=saved_offer.equity_risk_level,
            message=saved_offer.equity_message,
            P25=saved_offer.equity_p25,
            P50=saved_offer.equity_p50,
            P75=saved_offer.equity_p75,
            inversionDetected=saved_offer.inversion_detected,
        ),
        reportMarkdown=saved_offer.report_markdown,
    )


@router.post("/{offer_id}/outcome", response_model=OfferDetailResponse)
async def update_offer_outcome(
    offer_id: str,
    request: UpdateOfferOutcomeRequest,
    session: Session = Depends(get_db_session),
) -> OfferDetailResponse:
    offer_repository = OfferRepository(session)
    saved_offer = offer_repository.update_outcome(
        offer_id=offer_id,
        outcome_status=request.outcome_status,
        outcome_notes=request.outcome_notes or "",
    )
    return OfferDetailResponse(
        offerId=saved_offer.id,
        candidateId=saved_offer.candidate_id,
        marketSnapshotId=saved_offer.market_snapshot_id,
        strategyId=saved_offer.strategy_id,
        outcomeStatus=saved_offer.outcome_status,
        outcomeNotes=saved_offer.outcome_notes,
        decidedAt=saved_offer.decided_at,
        recommendedOffer=saved_offer.recommended_salary,
        range=OfferRangeResponse(min=saved_offer.range_min, max=saved_offer.range_max),
        crValue=saved_offer.cr_value,
        acceptProbability=saved_offer.accept_probability.quantize(Decimal("0.01")),
        acceptanceModelVersion=saved_offer.acceptance_model_version,
        competitivenessScore=saved_offer.competitiveness_score,
        confidence=saved_offer.confidence,
        riskLevel=saved_offer.overall_risk_level,
        riskReasons=saved_offer.risk_reasons,
        budget=BudgetAssessmentResponse(
            usageRatio=saved_offer.budget_usage_ratio,
            riskLevel=saved_offer.budget_risk_level,
            exceeded=saved_offer.budget_usage_ratio > Decimal("1.0000"),
        ),
        equity=EquityAssessmentResponse(
            equityScore=saved_offer.equity_score,
            riskLevel=saved_offer.equity_risk_level,
            message=saved_offer.equity_message,
            P25=saved_offer.equity_p25,
            P50=saved_offer.equity_p50,
            P75=saved_offer.equity_p75,
            inversionDetected=saved_offer.inversion_detected,
        ),
        reportMarkdown=saved_offer.report_markdown,
    )


@router.get("", response_model=list[OfferDetailResponse])
async def list_offers(
    candidate_id: str | None = Query(default=None, alias="candidateId"),
    strategy_id: str | None = Query(default=None, alias="strategyId"),
    risk_level: str | None = Query(default=None, alias="riskLevel"),
    session: Session = Depends(get_db_session),
) -> list[OfferDetailResponse]:
    offer_repository = OfferRepository(session)
    offers = offer_repository.list_offers(
        candidate_id=candidate_id,
        strategy_id=strategy_id,
        risk_level=risk_level,
    )
    return [
        OfferDetailResponse(
            offerId=offer.id,
            candidateId=offer.candidate_id,
            marketSnapshotId=offer.market_snapshot_id,
            strategyId=offer.strategy_id,
            outcomeStatus=offer.outcome_status,
            outcomeNotes=offer.outcome_notes,
            decidedAt=offer.decided_at,
            recommendedOffer=offer.recommended_salary,
            range=OfferRangeResponse(min=offer.range_min, max=offer.range_max),
            crValue=offer.cr_value,
            acceptProbability=offer.accept_probability.quantize(Decimal("0.01")),
            acceptanceModelVersion=offer.acceptance_model_version,
            competitivenessScore=offer.competitiveness_score,
            confidence=offer.confidence,
            riskLevel=offer.overall_risk_level,
            riskReasons=offer.risk_reasons,
            budget=BudgetAssessmentResponse(
                usageRatio=offer.budget_usage_ratio,
                riskLevel=offer.budget_risk_level,
                exceeded=offer.budget_usage_ratio > Decimal("1.0000"),
            ),
            equity=EquityAssessmentResponse(
                equityScore=offer.equity_score,
                riskLevel=offer.equity_risk_level,
                message=offer.equity_message,
                P25=offer.equity_p25,
                P50=offer.equity_p50,
                P75=offer.equity_p75,
                inversionDetected=offer.inversion_detected,
            ),
            reportMarkdown=offer.report_markdown,
        )
        for offer in offers
    ]

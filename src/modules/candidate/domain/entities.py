from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CandidateProfile:
    id: str
    company_id: str
    department_id: str
    position_id: str
    name: str
    current_salary: Decimal
    expected_salary: Decimal | None
    years_experience: int
    level: str
    skills: list[str]
    interview_score: int
    has_other_offer: bool
    city: str

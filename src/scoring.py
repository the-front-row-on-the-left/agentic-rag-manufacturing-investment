from __future__ import annotations

from collections import OrderedDict

from src.schemas import CriterionAssessment, InvestmentDecision, InvestmentDecisionDraft


WEIGHTS = OrderedDict(
    [
        ("problem_fit", 15),
        ("market_opportunity", 15),
        ("technology", 15),
        ("deployability", 15),
        ("data_availability", 5),
        ("integration", 10),
        ("scalability", 10),
        ("team_capability", 5),
        ("risk_assessment", 10),
    ]
)

LABELS = {
    "problem_fit": "문제 적합성",
    "market_opportunity": "시장성",
    "technology": "기술 경쟁력",
    "deployability": "현장 적용 가능성",
    "data_availability": "데이터 확보 가능성",
    "integration": "시스템 통합 가능성",
    "scalability": "확장 가능성",
    "team_capability": "팀 역량",
    "risk_assessment": "리스크 관리 수준",
}


def _weighted_score(raw_score: int, weight: int) -> float:
    return round((int(raw_score) / 5.0) * weight, 2)


def finalize_investment_decision(draft: InvestmentDecisionDraft) -> InvestmentDecision:
    score_breakdown: dict[str, CriterionAssessment] = {}
    total_score = 0.0

    for field_name, weight in WEIGHTS.items():
        criterion = getattr(draft, field_name)
        clamped_raw_score = max(1, min(5, int(criterion.raw_score)))
        weighted = _weighted_score(clamped_raw_score, weight)
        score_breakdown[field_name] = CriterionAssessment(
            raw_score=clamped_raw_score,
            weighted_score=weighted,
            reason=criterion.reason,
        )
        total_score += weighted

    total_score = round(total_score, 2)

    if total_score >= 80:
        decision = "recommend"
    elif total_score >= 65:
        decision = "conditional_review"
    else:
        decision = "hold"

    return InvestmentDecision(
        total_score=total_score,
        score_breakdown=score_breakdown,
        decision=decision,
        pros=draft.pros,
        cons=draft.cons,
        conditions=draft.conditions,
    )

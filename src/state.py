from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from src.schemas import (
    CompetitorAnalysis,
    InvestmentDecision,
    MarketAnalysis,
    StartupCandidate,
    StartupProfile,
    TechAnalysis,
)


class GraphState(TypedDict, total=False):
    # 사용자 입력
    input_keyword: str
    domain: str
    max_candidates: int

    # 스타트업 후보 관리
    candidate_startups: list[StartupCandidate]
    current_index: int
    # selected_startup is the candidate currently being evaluated, not the final recommendation.
    selected_startup: StartupCandidate | None

    # 기업 요약 정보
    startup_profile: StartupProfile | None

    # 기술 분석 결과
    tech_analysis: TechAnalysis | None
    tech_references: list[str]

    # 시장성 분석 결과
    market_analysis: MarketAnalysis | None
    market_references: list[str]

    # 경쟁 분석 결과
    competitor_analysis: CompetitorAnalysis | None
    competitor_references: list[str]

    # 투자 판단 결과
    investment_decision: InvestmentDecision | None

    # 누적 평가 결과
    recommended_startups: list[dict[str, Any]]
    held_startups: list[dict[str, Any]]

    # 보고서 출력
    references: list[str]
    final_report_markdown: str

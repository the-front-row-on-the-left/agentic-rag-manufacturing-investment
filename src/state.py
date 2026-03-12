from __future__ import annotations

from operator import add
from typing import Annotated, Any

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
    # User input
    input_keyword: str
    domain: str
    max_candidates: int

    # Candidate pool and selection state
    candidate_startups: list[StartupCandidate]
    current_index: int
    selected_startup: StartupCandidate | None
    search_done: bool

    # Current candidate outputs (reset when selected_startup changes)
    startup_profile: StartupProfile | None
    tech_analysis: TechAnalysis | None
    tech_references: list[str]
    market_analysis: MarketAnalysis | None
    market_references: list[str]
    competitor_analysis: CompetitorAnalysis | None
    competitor_references: list[str]
    investment_decision: InvestmentDecision | None

    # Aggregated history across all evaluated candidates
    recommended_startups: Annotated[list[dict[str, Any]], add]
    held_startups: Annotated[list[dict[str, Any]], add]
    evaluation_history: Annotated[list[dict[str, Any]], add]
    references: Annotated[list[str], add]

    # Final output
    final_report_markdown: str
